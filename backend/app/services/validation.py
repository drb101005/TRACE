"""Data validation and quality assessment service."""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

from app.domain.schemas import ValidationResult
from app.core.errors import ValidationException


class ValidationService:
    """Validate uploaded data for completeness and quality."""
    
    REQUIRED_SALES_COLUMNS = [
        "invoice_number", "invoice_date", "customer_name", "amount"
    ]
    
    OPTIONAL_SALES_COLUMNS = [
        "customer_id", "gross_amount", "tax_amount", "net_amount",
        "product", "quantity", "dispatch_date", "delivery_date"
    ]
    
    REQUIRED_RELATED_PARTY_COLUMNS = [
        "party_name"
    ]
    
    def validate_sales_register(
        self,
        df: pd.DataFrame,
        reporting_period_start: datetime,
        reporting_period_end: datetime
    ) -> ValidationResult:
        """Validate sales register data."""
        errors = []
        warnings = []
        missing_fields = []
        
        # Check required columns (case-insensitive)
        df_columns_lower = [col.lower() for col in df.columns]
        column_mapping = {col.lower(): col for col in df.columns}
        
        for req_col in self.REQUIRED_SALES_COLUMNS:
            if req_col not in df_columns_lower:
                missing_fields.append(req_col)
                errors.append(f"Required column '{req_col}' not found")
        
        if errors:
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                missing_fields=missing_fields,
                total_records=len(df)
            )
        
        # Map to standard columns
        std_df = pd.DataFrame()
        for std_name in self.REQUIRED_SALES_COLUMNS + self.OPTIONAL_SALES_COLUMNS:
            if std_name in df_columns_lower:
                actual_col = column_mapping[std_name]
                std_df[std_name] = df[actual_col]
        
        # Validate data types and values
        errors_found, warnings_found = self._validate_sales_data(
            std_df, reporting_period_start, reporting_period_end
        )
        errors.extend(errors_found)
        warnings.extend(warnings_found)
        
        # Check for duplicate candidates
        duplicate_candidates = self._find_duplicate_candidates(std_df)
        
        # Calculate totals
        total_records = len(std_df)
        total_amount = self._calculate_total_amount(std_df)
        
        # Check date coverage
        date_range = self._analyze_date_coverage(
            std_df, reporting_period_start, reporting_period_end
        )
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            duplicate_candidates=duplicate_candidates,
            total_records=total_records,
            total_amount=total_amount,
            date_range=date_range,
            missing_fields=missing_fields
        )
    
    def _validate_sales_data(
        self,
        df: pd.DataFrame,
        period_start: datetime,
        period_end: datetime
    ) -> Tuple[List[str], List[str]]:
        """Validate sales data quality."""
        errors = []
        warnings = []
        
        # Validate invoice numbers
        if "invoice_number" in df.columns:
            null_invoices = df["invoice_number"].isna().sum()
            if null_invoices > 0:
                errors.append(f"{null_invoices} records with missing invoice number")
            
            # Check for empty strings
            empty_invoices = (df["invoice_number"].astype(str).str.strip() == "").sum()
            if empty_invoices > 0:
                errors.append(f"{empty_invoices} records with empty invoice number")
        
        # Validate dates
        if "invoice_date" in df.columns:
            try:
                df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
                null_dates = df["invoice_date"].isna().sum()
                if null_dates > 0:
                    warnings.append(f"{null_dates} records with invalid or missing invoice date")
            except Exception as e:
                errors.append(f"Failed to parse invoice dates: {str(e)}")
        
        # Validate amounts
        if "amount" in df.columns:
            try:
                df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
                null_amounts = df["amount"].isna().sum()
                if null_amounts > 0:
                    warnings.append(f"{null_amounts} records with invalid or missing amount")
                
                negative_amounts = (df["amount"] < 0).sum()
                if negative_amounts > 0:
                    warnings.append(f"{negative_amounts} records with negative amount")
                
                zero_amounts = (df["amount"] == 0).sum()
                if zero_amounts > 0:
                    warnings.append(f"{zero_amounts} records with zero amount")
            except Exception as e:
                errors.append(f"Failed to parse amounts: {str(e)}")
        
        # Validate customer names
        if "customer_name" in df.columns:
            null_customers = df["customer_name"].isna().sum()
            if null_customers > 0:
                warnings.append(f"{null_customers} records with missing customer name")
        
        return errors, warnings
    
    def _find_duplicate_candidates(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find potential duplicate records."""
        duplicates = []
        
        if "invoice_number" in df.columns:
            # Find duplicate invoice numbers
            dup_invoices = df[df.duplicated(subset=["invoice_number"], keep=False)]
            if not dup_invoices.empty:
                for invoice_num in dup_invoices["invoice_number"].unique():
                    dup_group = df[df["invoice_number"] == invoice_num]
                    duplicates.append({
                        "type": "duplicate_invoice_number",
                        "invoice_number": invoice_num,
                        "count": len(dup_group),
                        "indices": dup_group.index.tolist()
                    })
        
        return duplicates
    
    def _calculate_total_amount(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate total amount from dataframe."""
        amount_col = None
        for col in ["amount", "gross_amount", "net_amount"]:
            if col in df.columns:
                amount_col = col
                break
        
        if amount_col:
            try:
                df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
                return float(df[amount_col].sum())
            except Exception:
                return None
        
        return None
    
    def _analyze_date_coverage(
        self,
        df: pd.DataFrame,
        period_start: datetime,
        period_end: datetime
    ) -> Optional[Dict[str, Any]]:
        """Analyze date coverage against reporting period."""
        if "invoice_date" not in df.columns:
            return None
        
        try:
            df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
            valid_dates = df[df["invoice_date"].notna()]
            
            if valid_dates.empty:
                return {"error": "No valid dates found"}
            
            min_date = valid_dates["invoice_date"].min()
            max_date = valid_dates["invoice_date"].max()
            
            # Count records in period
            in_period = valid_dates[
                (valid_dates["invoice_date"] >= period_start) &
                (valid_dates["invoice_date"] <= period_end)
            ]
            
            before_period = valid_dates[valid_dates["invoice_date"] < period_start]
            after_period = valid_dates[valid_dates["invoice_date"] > period_end]
            
            return {
                "min_date": min_date.isoformat(),
                "max_date": max_date.isoformat(),
                "records_in_period": len(in_period),
                "records_before_period": len(before_period),
                "records_after_period": len(after_period),
                "coverage_complete": len(before_period) == 0 and len(after_period) == 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def validate_related_parties(self, df: pd.DataFrame) -> ValidationResult:
        """Validate related party master data."""
        errors = []
        warnings = []
        
        # Check required columns
        df_columns_lower = [col.lower() for col in df.columns]
        
        for req_col in self.REQUIRED_RELATED_PARTY_COLUMNS:
            if req_col not in df_columns_lower:
                errors.append(f"Required column '{req_col}' not found")
        
        if errors:
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                total_records=len(df)
            )
        
        # Map columns
        column_mapping = {col.lower(): col for col in df.columns}
        party_col = column_mapping.get("party_name")
        
        # Check for missing party names
        if party_col:
            null_parties = df[party_col].isna().sum()
            if null_parties > 0:
                warnings.append(f"{null_parties} records with missing party name")
            
            # Check for duplicates
            dup_parties = df[df.duplicated(subset=[party_col], keep=False)]
            if not dup_parties.empty:
                warnings.append(
                    f"{len(dup_parties)} duplicate party names found"
                )
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            total_records=len(df)
        )
