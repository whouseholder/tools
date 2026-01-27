"""Visualization engine for tables and charts."""

from typing import Any, Dict, List, Optional
import json

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from loguru import logger

from ..llm.llm_manager import LLMManager
from ..utils.config import VisualizationConfig


class VisualizationEngine:
    """Creates visualizations from query results."""
    
    def __init__(
        self,
        llm_manager: LLMManager,
        config: VisualizationConfig
    ):
        """Initialize visualization engine."""
        self.llm_manager = llm_manager
        self.config = config
        logger.info("Visualization engine initialized")
    
    def create_table(
        self,
        columns: List[str],
        rows: List[tuple]
    ) -> Dict[str, Any]:
        """
        Create a table visualization.
        
        Returns dict with 'type', 'data', and 'html'.
        """
        df = pd.DataFrame(rows, columns=columns)
        
        # Create Plotly table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df.columns),
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=[df[col] for col in df.columns],
                fill_color='lavender',
                align='left',
                font=dict(size=11, color='black')
            )
        )])
        
        fig.update_layout(
            title="Query Results",
            height=min(600, 50 + len(rows) * 30)
        )
        
        logger.info(f"Created table visualization: {len(rows)} rows x {len(columns)} columns")
        
        return {
            'type': 'table',
            'data': {
                'columns': columns,
                'rows': [list(row) for row in rows]
            },
            'html': fig.to_html(),
            'json': fig.to_json()
        }
    
    def create_chart(
        self,
        columns: List[str],
        rows: List[tuple],
        chart_type: Optional[str] = None,
        sql_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a chart visualization.
        
        If chart_type is None, uses LLM to suggest best chart type.
        
        Returns dict with 'type', 'chart_type', 'data', and 'html'.
        """
        df = pd.DataFrame(rows, columns=columns)
        
        # Determine chart type if not provided
        if chart_type is None and self.config.auto_suggest_charts:
            chart_type = self._suggest_chart_type(columns, df, sql_query)
        elif chart_type is None:
            chart_type = 'bar'  # Default
        
        # Validate chart type
        if chart_type not in self.config.supported_chart_types:
            logger.warning(f"Unsupported chart type: {chart_type}, using bar chart")
            chart_type = 'bar'
        
        # Create chart based on type
        try:
            fig = self._create_chart_figure(df, chart_type)
            
            logger.info(f"Created {chart_type} chart visualization")
            
            return {
                'type': 'chart',
                'chart_type': chart_type,
                'data': {
                    'columns': columns,
                    'rows': [list(row) for row in rows]
                },
                'html': fig.to_html(),
                'json': fig.to_json()
            }
            
        except Exception as e:
            logger.error(f"Chart creation failed: {e}, falling back to table")
            return self.create_table(columns, rows)
    
    def _suggest_chart_type(
        self,
        columns: List[str],
        df: pd.DataFrame,
        sql_query: Optional[str] = None
    ) -> str:
        """Use LLM to suggest best chart type based on query structure."""
        # Analyze data structure
        data_info = {
            'columns': columns,
            'num_columns': len(columns),
            'num_rows': len(df),
            'column_types': {col: str(df[col].dtype) for col in columns}
        }
        
        prompt = f"""Given the following query results structure, suggest the BEST chart type for visualization.

Data Structure:
- Columns: {data_info['columns']}
- Number of columns: {data_info['num_columns']}
- Number of rows: {data_info['num_rows']}
- Column types: {data_info['column_types']}

{f"SQL Query: {sql_query}" if sql_query else ""}

Available chart types: {', '.join(self.config.supported_chart_types)}

Respond with ONLY ONE of the chart types from the list above, nothing else."""
        
        try:
            suggestion = self.llm_manager.generate(
                prompt=prompt,
                system_prompt="You are a data visualization expert. Suggest the most appropriate chart type.",
                use_large_model=False
            ).strip().lower()
            
            # Validate suggestion
            if suggestion in self.config.supported_chart_types:
                logger.info(f"LLM suggested chart type: {suggestion}")
                return suggestion
            else:
                logger.warning(f"Invalid LLM suggestion: {suggestion}, using bar chart")
                return 'bar'
                
        except Exception as e:
            logger.error(f"Chart type suggestion failed: {e}, using bar chart")
            return 'bar'
    
    def _create_chart_figure(
        self,
        df: pd.DataFrame,
        chart_type: str
    ) -> go.Figure:
        """Create Plotly figure based on chart type."""
        if chart_type == 'bar':
            return self._create_bar_chart(df)
        elif chart_type == 'line':
            return self._create_line_chart(df)
        elif chart_type == 'scatter':
            return self._create_scatter_chart(df)
        elif chart_type == 'pie':
            return self._create_pie_chart(df)
        elif chart_type == 'heatmap':
            return self._create_heatmap(df)
        elif chart_type == 'histogram':
            return self._create_histogram(df)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
    
    def _create_bar_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create bar chart."""
        if len(df.columns) >= 2:
            x_col = df.columns[0]
            y_col = df.columns[1]
            fig = px.bar(df, x=x_col, y=y_col, title="Bar Chart")
        else:
            fig = px.bar(df, title="Bar Chart")
        return fig
    
    def _create_line_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create line chart."""
        if len(df.columns) >= 2:
            x_col = df.columns[0]
            y_cols = df.columns[1:]
            fig = px.line(df, x=x_col, y=y_cols, title="Line Chart")
        else:
            fig = px.line(df, title="Line Chart")
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create scatter plot."""
        if len(df.columns) >= 2:
            x_col = df.columns[0]
            y_col = df.columns[1]
            fig = px.scatter(df, x=x_col, y=y_col, title="Scatter Plot")
        else:
            fig = px.scatter(df, title="Scatter Plot")
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create pie chart."""
        if len(df.columns) >= 2:
            names_col = df.columns[0]
            values_col = df.columns[1]
            fig = px.pie(df, names=names_col, values=values_col, title="Pie Chart")
        else:
            fig = go.Figure(data=[go.Pie()])
        return fig
    
    def _create_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """Create heatmap."""
        # Select only numeric columns
        numeric_df = df.select_dtypes(include=['number'])
        
        if not numeric_df.empty:
            fig = px.imshow(
                numeric_df.corr() if len(numeric_df.columns) > 1 else numeric_df,
                title="Heatmap",
                aspect="auto"
            )
        else:
            fig = go.Figure(data=[go.Heatmap()])
        return fig
    
    def _create_histogram(self, df: pd.DataFrame) -> go.Figure:
        """Create histogram."""
        # Use first numeric column
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            fig = px.histogram(df, x=col, title="Histogram")
        else:
            fig = go.Figure(data=[go.Histogram()])
        return fig
