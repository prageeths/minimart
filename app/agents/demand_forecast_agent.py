"""Demand Forecast Agent for predicting product demand."""

import asyncio
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import openai
from app.agents.base_agent import BaseAgent
from app.models.models import AgentType, Product, SalesTransaction
from app.database.database import SessionLocal
from app.core.config import settings

# Set OpenAI API key
openai.api_key = settings.openai_api_key


class DemandForecastAgent(BaseAgent):
    """Agent responsible for demand forecasting using historical data and market analysis."""
    
    def __init__(self):
        super().__init__(AgentType.DEMAND_FORECAST)
        self.forecast_horizon_days = 90  # Forecast for next 90 days
        self.seasonality_periods = {
            'daily': 7,    # Weekly seasonality
            'weekly': 52,  # Yearly seasonality
            'monthly': 12  # Yearly seasonality
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute demand forecasting for given products."""
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            if not self.validate_input(input_data, ['product_ids', 'forecast_period_days']):
                return self.create_error_response("Invalid input data")
            
            product_ids = input_data['product_ids']
            forecast_period_days = input_data.get('forecast_period_days', self.forecast_horizon_days)
            
            # Get historical data
            historical_data = await self._get_historical_sales_data(product_ids)
            
            # Perform forecasting for each product
            forecasts = {}
            for product_id in product_ids:
                if product_id in historical_data:
                    forecast = await self._forecast_product_demand(
                        product_id, 
                        historical_data[product_id], 
                        forecast_period_days
                    )
                    forecasts[product_id] = forecast
            
            # Get market insights from OpenAI
            market_insights = await self._get_market_insights(product_ids)
            
            # Combine forecasts with market insights
            enhanced_forecasts = await self._enhance_forecasts_with_market_data(forecasts, market_insights)
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'forecasts': enhanced_forecasts,
                'market_insights': market_insights,
                'forecast_period_days': forecast_period_days,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Log the action
            await self.log_action(
                action="demand_forecast",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        except Exception as e:
            self.logger.error(f"Error in demand forecasting: {e}")
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self.log_action(
                action="demand_forecast",
                input_data=input_data,
                output_data={},
                status="error",
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
            return self.create_error_response(f"Demand forecasting failed: {str(e)}")
    
    async def _get_historical_sales_data(self, product_ids: List[int]) -> Dict[int, pd.DataFrame]:
        """Retrieve historical sales data for products."""
        db = SessionLocal()
        try:
            # Get sales data for the last 5 years
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=5*365)
            
            sales_data = db.query(SalesTransaction).filter(
                SalesTransaction.product_id.in_(product_ids),
                SalesTransaction.transaction_date >= start_date,
                SalesTransaction.transaction_date <= end_date
            ).all()
            
            # Convert to DataFrame format
            historical_data = {}
            for product_id in product_ids:
                product_sales = [s for s in sales_data if s.product_id == product_id]
                
                if product_sales:
                    df_data = []
                    for sale in product_sales:
                        df_data.append({
                            'date': sale.transaction_date.date(),
                            'quantity': sale.quantity,
                            'revenue': sale.total_amount
                        })
                    
                    df = pd.DataFrame(df_data)
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                    df = df.resample('D').sum().fillna(0)  # Daily aggregation
                    
                    historical_data[product_id] = df
                else:
                    # Create empty DataFrame for products with no sales history
                    historical_data[product_id] = pd.DataFrame(columns=['quantity', 'revenue'])
            
            return historical_data
            
        finally:
            db.close()
    
    async def _forecast_product_demand(
        self, 
        product_id: int, 
        historical_data: pd.DataFrame, 
        forecast_days: int
    ) -> Dict[str, Any]:
        """Forecast demand for a specific product using multiple methods."""
        
        if historical_data.empty or len(historical_data) < 30:
            # Not enough data for sophisticated forecasting
            return await self._simple_forecast(product_id, historical_data, forecast_days)
        
        try:
            # Method 1: Exponential Smoothing
            exp_smoothing_forecast = await self._exponential_smoothing_forecast(
                historical_data['quantity'], forecast_days
            )
            
            # Method 2: Seasonal Decomposition
            seasonal_forecast = await self._seasonal_decomposition_forecast(
                historical_data['quantity'], forecast_days
            )
            
            # Method 3: Linear Regression with Polynomial Features
            regression_forecast = await self._regression_forecast(
                historical_data['quantity'], forecast_days
            )
            
            # Combine forecasts using weighted average
            combined_forecast = self._combine_forecasts([
                exp_smoothing_forecast,
                seasonal_forecast,
                regression_forecast
            ])
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                historical_data['quantity'], combined_forecast
            )
            
            return {
                'product_id': product_id,
                'forecast_methods': {
                    'exponential_smoothing': exp_smoothing_forecast,
                    'seasonal_decomposition': seasonal_forecast,
                    'regression': regression_forecast
                },
                'combined_forecast': combined_forecast,
                'confidence_intervals': confidence_intervals,
                'forecast_period_days': forecast_days,
                'data_quality': 'good' if len(historical_data) >= 90 else 'limited'
            }
            
        except Exception as e:
            self.logger.warning(f"Advanced forecasting failed for product {product_id}: {e}")
            return await self._simple_forecast(product_id, historical_data, forecast_days)
    
    async def _exponential_smoothing_forecast(
        self, 
        data: pd.Series, 
        forecast_days: int
    ) -> List[float]:
        """Forecast using exponential smoothing."""
        try:
            model = ExponentialSmoothing(
                data, 
                trend='add', 
                seasonal='add', 
                seasonal_periods=7
            ).fit()
            forecast = model.forecast(forecast_days)
            return forecast.tolist()
        except:
            # Fallback to simple exponential smoothing
            model = ExponentialSmoothing(data, trend='add').fit()
            forecast = model.forecast(forecast_days)
            return forecast.tolist()
    
    async def _seasonal_decomposition_forecast(
        self, 
        data: pd.Series, 
        forecast_days: int
    ) -> List[float]:
        """Forecast using seasonal decomposition."""
        try:
            decomposition = seasonal_decompose(data, model='additive', period=7)
            trend = decomposition.trend.dropna()
            seasonal = decomposition.seasonal
            
            # Simple linear trend extrapolation
            if len(trend) > 1:
                x = np.arange(len(trend))
                y = trend.values
                model = LinearRegression().fit(x.reshape(-1, 1), y)
                
                # Forecast trend
                future_x = np.arange(len(trend), len(trend) + forecast_days)
                trend_forecast = model.predict(future_x.reshape(-1, 1))
                
                # Add seasonal component
                seasonal_pattern = seasonal.iloc[-7:].values  # Last week's pattern
                seasonal_forecast = np.tile(seasonal_pattern, (forecast_days // 7) + 1)[:forecast_days]
                
                return (trend_forecast + seasonal_forecast).tolist()
            else:
                return [data.mean()] * forecast_days
                
        except Exception as e:
            self.logger.warning(f"Seasonal decomposition failed: {e}")
            return [data.mean()] * forecast_days
    
    async def _regression_forecast(
        self, 
        data: pd.Series, 
        forecast_days: int
    ) -> List[float]:
        """Forecast using polynomial regression."""
        try:
            if len(data) < 10:
                return [data.mean()] * forecast_days
            
            # Create features: time, time^2, day_of_week
            x = np.arange(len(data))
            day_of_week = pd.to_datetime(data.index).dayofweek
            
            # Polynomial features
            poly = PolynomialFeatures(degree=2)
            X = poly.fit_transform(x.reshape(-1, 1))
            X = np.column_stack([X, day_of_week])
            
            model = LinearRegression().fit(X, data.values)
            
            # Forecast
            future_x = np.arange(len(data), len(data) + forecast_days)
            future_day_of_week = [(pd.Timestamp.now() + timedelta(days=i)).dayofweek 
                                 for i in range(forecast_days)]
            
            future_X = poly.fit_transform(future_x.reshape(-1, 1))
            future_X = np.column_stack([future_X, future_day_of_week])
            
            forecast = model.predict(future_X)
            return forecast.tolist()
            
        except Exception as e:
            self.logger.warning(f"Regression forecasting failed: {e}")
            return [data.mean()] * forecast_days
    
    async def _simple_forecast(
        self, 
        product_id: int, 
        historical_data: pd.DataFrame, 
        forecast_days: int
    ) -> Dict[str, Any]:
        """Simple forecasting for products with limited data."""
        if historical_data.empty:
            # No historical data - use default assumptions
            default_daily_demand = 5  # Assume 5 units per day
            forecast = [default_daily_demand] * forecast_days
        else:
            # Use simple average with slight trend
            avg_daily = historical_data['quantity'].mean()
            recent_avg = historical_data['quantity'].tail(7).mean()
            
            # Simple trend calculation
            if len(historical_data) >= 14:
                old_avg = historical_data['quantity'].head(7).mean()
                trend = (recent_avg - old_avg) / 7  # Daily trend
            else:
                trend = 0
            
            # Generate forecast with trend
            forecast = []
            for i in range(forecast_days):
                daily_forecast = max(0, avg_daily + (trend * i))
                forecast.append(daily_forecast)
        
        return {
            'product_id': product_id,
            'forecast_methods': {
                'simple_average': forecast
            },
            'combined_forecast': forecast,
            'confidence_intervals': {
                'lower': [max(0, x * 0.7) for x in forecast],
                'upper': [x * 1.3 for x in forecast]
            },
            'forecast_period_days': forecast_days,
            'data_quality': 'limited'
        }
    
    def _combine_forecasts(self, forecasts: List[List[float]]) -> List[float]:
        """Combine multiple forecasts using weighted average."""
        if not forecasts:
            return []
        
        # Equal weights for now - could be improved with model performance tracking
        weights = [1.0 / len(forecasts)] * len(forecasts)
        
        combined = []
        for i in range(len(forecasts[0])):
            weighted_sum = sum(forecast[i] * weight for forecast, weight in zip(forecasts, weights))
            combined.append(weighted_sum)
        
        return combined
    
    def _calculate_confidence_intervals(
        self, 
        historical_data: pd.Series, 
        forecast: List[float]
    ) -> Dict[str, List[float]]:
        """Calculate confidence intervals for the forecast."""
        if len(historical_data) < 2:
            return {
                'lower': [max(0, x * 0.5) for x in forecast],
                'upper': [x * 1.5 for x in forecast]
            }
        
        # Calculate historical volatility
        returns = historical_data.pct_change().dropna()
        volatility = returns.std()
        
        # Simple confidence intervals based on volatility
        lower = [max(0, x * (1 - 2 * volatility)) for x in forecast]
        upper = [x * (1 + 2 * volatility) for x in forecast]
        
        return {'lower': lower, 'upper': upper}
    
    async def _get_market_insights(self, product_ids: List[int]) -> Dict[str, Any]:
        """Get market insights using OpenAI API."""
        try:
            # Get product information
            db = SessionLocal()
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            db.close()
            
            if not products:
                return {}
            
            # Create prompt for market analysis
            product_names = [p.name for p in products]
            prompt = f"""
            Analyze the market trends and demand factors for the following mini mart products:
            {', '.join(product_names)}
            
            Consider:
            1. Seasonal trends and patterns
            2. Economic factors affecting demand
            3. Consumer behavior changes
            4. Competitive landscape
            5. External factors (weather, events, etc.)
            
            Provide insights that could affect demand forecasting for the next 90 days.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            market_analysis = response.choices[0].message.content
            
            return {
                'analysis': market_analysis,
                'generated_at': datetime.utcnow().isoformat(),
                'products_analyzed': product_names
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to get market insights: {e}")
            return {
                'analysis': 'Market analysis unavailable',
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    async def _enhance_forecasts_with_market_data(
        self, 
        forecasts: Dict[int, Dict[str, Any]], 
        market_insights: Dict[str, Any]
    ) -> Dict[int, Dict[str, Any]]:
        """Enhance forecasts with market insights."""
        # For now, return forecasts as-is
        # In a more sophisticated implementation, this would adjust forecasts
        # based on market insights using NLP and sentiment analysis
        
        for product_id, forecast in forecasts.items():
            forecast['market_insights'] = market_insights
        
        return forecasts
