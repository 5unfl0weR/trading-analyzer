"""Chart image analysis and pattern recognition."""

import streamlit as st
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import requests
import base64
from io import BytesIO

class ChartAnalyzer:
    def __init__(self):
        self.patterns = {
            "trend_lines": [],
            "support_resistance": [],
            "candlestick_patterns": [],
            "indicators": []
        }
    
    def analyze_uploaded_chart(self, uploaded_file):
        """Main function to analyze uploaded chart image."""
        if uploaded_file is not None:
            # Load and process image
            image = Image.open(uploaded_file)
            
            # Display original image
            st.image(image, caption="Uploaded Chart", use_container_width=True)
            
            # Convert to array for processing
            img_array = np.array(image)
            
            # Perform analysis
            analysis_results = self.perform_chart_analysis(img_array, image)
            
            return analysis_results
        return None
    
    def perform_chart_analysis(self, img_array, original_image):
        """Analyze the chart image for trading signals."""
        
        # Initialize results
        results = {
            "overall_signal": "HOLD",
            "confidence": 0,
            "trend_direction": "NEUTRAL",
            "support_resistance": [],
            "patterns_detected": [],
            "technical_analysis": {},
            "recommendation": ""
        }
        
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Detect edges (price movements, trend lines)
            edges = cv2.Canny(gray, 50, 150)
            
            # Analyze price movement direction
            trend_analysis = self.analyze_trend_direction(gray)
            results["trend_direction"] = trend_analysis["direction"]
            results["confidence"] = trend_analysis["confidence"]
            
            # Detect chart patterns
            patterns = self.detect_chart_patterns(gray, edges)
            results["patterns_detected"] = patterns
            
            # Analyze support/resistance levels
            support_resistance = self.find_support_resistance_levels(gray)
            results["support_resistance"] = support_resistance
            
            # Generate overall trading signal
            signal_analysis = self.generate_trading_signal(results)
            results.update(signal_analysis)
            
            # Add technical analysis insights
            results["technical_analysis"] = self.generate_technical_insights(results)
            
        except Exception as e:
            st.error(f"Error analyzing chart: {str(e)}")
            results["recommendation"] = "Unable to analyze chart. Please try a clearer image."
        
        return results
    
    def analyze_trend_direction(self, gray_image):
        """Analyze overall trend direction from the chart."""
        height, width = gray_image.shape
        
        # Sample price points from right side of chart (recent prices)
        recent_region = gray_image[:, int(width*0.7):]
        
        # Find the brightest pixels (likely price line/candles)
        bright_threshold = np.percentile(recent_region, 85)
        bright_pixels = np.where(recent_region > bright_threshold)
        
        if len(bright_pixels[0]) > 10:
            # Calculate slope of recent price movement
            y_coords = bright_pixels[0]
            x_coords = bright_pixels[1]
            
            # Fit line to recent price points
            if len(y_coords) > 1:
                slope = np.polyfit(x_coords, y_coords, 1)[0]
                
                # Determine trend (negative slope = uptrend in image coordinates)
                if slope < -2:
                    return {"direction": "STRONG_UPTREND", "confidence": 80}
                elif slope < -0.5:
                    return {"direction": "UPTREND", "confidence": 65}
                elif slope > 2:
                    return {"direction": "STRONG_DOWNTREND", "confidence": 80}
                elif slope > 0.5:
                    return {"direction": "DOWNTREND", "confidence": 65}
                else:
                    return {"direction": "SIDEWAYS", "confidence": 50}
        
        return {"direction": "NEUTRAL", "confidence": 30}
    
    def detect_chart_patterns(self, gray_image, edges):
        """Detect common chart patterns."""
        patterns = []
        
        # Find horizontal lines (support/resistance)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Count horizontal line strength
        horizontal_strength = np.sum(horizontal_lines > 0)
        
        if horizontal_strength > 100:
            patterns.append("Strong Support/Resistance Levels")
        
        # Detect triangular patterns (simplified)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if len(contour) > 10:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                if len(approx) == 3:
                    patterns.append("Triangle Pattern")
                elif len(approx) == 4:
                    patterns.append("Rectangle/Channel Pattern")
        
        return patterns[:5]  # Return top 5 patterns
    
    def find_support_resistance_levels(self, gray_image):
        """Find horizontal support and resistance levels."""
        height, width = gray_image.shape
        
        # Look for horizontal lines in price area
        horizontal_projection = np.sum(gray_image, axis=1)
        
        # Find peaks (potential support/resistance)
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(horizontal_projection, height=np.max(horizontal_projection)*0.3)
        
        levels = []
        for peak in peaks[:5]:  # Top 5 levels
            strength = horizontal_projection[peak]
            price_level = f"Level at {peak/height*100:.1f}% of chart height"
            levels.append({"level": price_level, "strength": int(strength)})
        
        return levels
    
    def generate_trading_signal(self, analysis_results):
        """Generate overall buy/sell signal based on analysis."""
        signal_score = 0
        reasoning = []
        
        # Trend analysis weight: 40%
        trend = analysis_results["trend_direction"]
        if "UPTREND" in trend:
            if "STRONG" in trend:
                signal_score += 40
                reasoning.append("Strong uptrend detected")
            else:
                signal_score += 25
                reasoning.append("Uptrend detected")
        elif "DOWNTREND" in trend:
            if "STRONG" in trend:
                signal_score -= 40
                reasoning.append("Strong downtrend detected")
            else:
                signal_score -= 25
                reasoning.append("Downtrend detected")
        
        # Pattern analysis weight: 30%
        patterns = analysis_results["patterns_detected"]
        for pattern in patterns:
            if "Triangle" in pattern:
                signal_score += 10
                reasoning.append("Triangle pattern suggests breakout potential")
            elif "Support" in pattern:
                signal_score += 15
                reasoning.append("Strong support/resistance levels identified")
        
        # Support/Resistance weight: 30%
        levels = analysis_results["support_resistance"]
        if len(levels) >= 3:
            signal_score += 10
            reasoning.append("Multiple support/resistance levels provide structure")
        
        # Determine final signal
        if signal_score >= 30:
            overall_signal = "STRONG BUY"
            confidence = min(90, 60 + signal_score)
        elif signal_score >= 15:
            overall_signal = "BUY"
            confidence = min(75, 50 + signal_score)
        elif signal_score <= -30:
            overall_signal = "STRONG SELL"
            confidence = min(90, 60 + abs(signal_score))
        elif signal_score <= -15:
            overall_signal = "SELL"
            confidence = min(75, 50 + abs(signal_score))
        else:
            overall_signal = "HOLD"
            confidence = 40 + abs(signal_score)
        
        recommendation = f"Based on technical analysis: {' | '.join(reasoning)}"
        
        return {
            "overall_signal": overall_signal,
            "confidence": confidence,
            "recommendation": recommendation,
            "signal_score": signal_score
        }
    
    def generate_technical_insights(self, results):
        """Generate detailed technical analysis insights."""
        insights = {}
        
        # Trend insights
        trend = results["trend_direction"]
        if "UPTREND" in trend:
            insights["trend_analysis"] = "Bullish momentum detected. Consider long positions."
        elif "DOWNTREND" in trend:
            insights["trend_analysis"] = "Bearish pressure evident. Consider short positions or exit longs."
        else:
            insights["trend_analysis"] = "Market consolidating. Wait for clear directional break."
        
        # Pattern insights
        patterns = results["patterns_detected"]
        if patterns:
            insights["pattern_analysis"] = f"Key patterns: {', '.join(patterns)}. Monitor for breakouts."
        else:
            insights["pattern_analysis"] = "No clear patterns detected. Market may be in transition."
        
        # Risk management
        levels = results["support_resistance"]
        if levels:
            insights["risk_management"] = f"Watch {len(levels)} key levels. Use them for stop-loss placement."
        else:
            insights["risk_management"] = "Limited clear levels. Use tight stops and small position sizes."
        
        return insights

# Add scipy to requirements if not present
try:
    from scipy.signal import find_peaks
except ImportError:
    def find_peaks(data, height=None):
        """Simple peak detection fallback."""
        peaks = []
        for i in range(1, len(data)-1):
            if data[i] > data[i-1] and data[i] > data[i+1]:
                if height is None or data[i] >= height:
                    peaks.append(i)
        return peaks, {}
