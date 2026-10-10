"""Deterministic hybrid sampling service."""
import random
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db import models
from app.domain.enums import SampleSelectionReason
from app.core.errors import SamplingException


class SamplingService:
    """
    Hybrid sampling combining:
    1. Deterministic risk-ranked selection
    2. Mandatory coverage rules
    3. Seeded random fill
    """
    
    ALGORITHM_VERSION = "1.0.0"
    DEFAULT_SALES_TOD_TARGET = 30
    CUTOFF_PRE_COUNT = 10
    CUTOFF_POST_COUNT_MIN = 10
    CUTOFF_POST_COUNT_MAX = 15
    
    def __init__(self, db: Session):
        self.db = db
    
    def select_sales_tod_sample(
        self,
        snapshot_id: str,
        target_count: int = DEFAULT_SALES_TOD_TARGET,
        random_seed: Optional[int] = None
    ) -> Tuple[List[models.Sample], Dict[str, Any]]:
        """
        Select Sales Test of Details (TOD) sample using hybrid approach.
        
        Returns: (samples, metadata)
        """
        # Get snapshot
        snapshot = self.db.query(models.PopulationSnapshot).filter(
            models.PopulationSnapshot.id == snapshot_id
        ).first()
        
        if not snapshot:
            raise SamplingException(f"Snapshot {snapshot_id} not found")
        
        # Get eligible transactions
        transactions = self._get_eligible_transactions(snapshot)
        
        if not transactions:
            raise SamplingException("No eligible transactions in snapshot")
        
        # Initialize random seed
        if random_seed is None:
            random_seed = random.randint(1, 999999)
        random.seed(random_seed)
        
        selected = []
        selection_metadata = {
            "high_risk_count": 0,
            "high_value_count": 0,
            "related_party_count": 0,
            "non_related_party_count": 0,
            "customer_diversity_count": 0,
            "random_fill_count": 0,
            "total_eligible": len(transactions)
        }
        
        # Step 1: Select high-risk transactions (top 20% by risk score)
        high_risk = self._select_high_risk(transactions, target_count // 3)
        selected.extend(high_risk)
        selection_metadata["high_risk_count"] = len(high_risk)
        
        # Step 2: Mandatory coverage - related party transactions
        related_party = self._select_related_party(
            transactions, selected, min_count=2
        )
        selected.extend(related_party)
        selection_metadata["related_party_count"] = len(related_party)
        
        # Step 3: Mandatory coverage - non-related party transactions
        non_related = self._select_non_related_party(
            transactions, selected, min_count=2
        )
        selected.extend(non_related)
        selection_metadata["non_related_party_count"] = len(non_related)
        
        # Step 4: High-value transactions (top 10% by amount)
        high_value = self._select_high_value(
            transactions, selected, target_count // 5
        )
        selected.extend(high_value)
        selection_metadata["high_value_count"] = len(high_value)
        
        # Step 5: Customer diversity (ensure multiple customers)
        diverse = self._select_customer_diversity(
            transactions, selected, min_customers=5
        )
        selected.extend(diverse)
        selection_metadata["customer_diversity_count"] = len(diverse)
        
        # Step 6: Random fill to reach target
        remaining_needed = max(0, target_count - len(selected))
        if remaining_needed > 0:
            random_fill = self._random_fill(
                transactions, selected, remaining_needed
            )
            selected.extend(random_fill)
            selection_metadata["random_fill_count"] = len(random_fill)
        
        # Create Sample objects
        samples = []
        for i, (txn, reasons, factors) in enumerate(selected):
            sample = models.Sample(
                transaction_id=txn.id,
                selection_reasons=reasons,
                risk_factors=factors,
                selection_order=i + 1
            )
            samples.append(sample)
        
        # Coverage summary
        actual_count = len(samples)
        shortfall = target_count - actual_count if actual_count < target_count else 0
        
        coverage_summary = self._generate_coverage_summary(
            selection_metadata, target_count, actual_count, shortfall
        )
        
        return samples, {
            "algorithm_version": self.ALGORITHM_VERSION,
            "random_seed": random_seed,
            "target_count": target_count,
            "actual_count": actual_count,
            "shortfall": shortfall,
            "selection_metadata": selection_metadata,
            "coverage_summary": coverage_summary
        }
    
    def select_cutoff_tod_sample(
        self,
        snapshot_id: str,
        cutoff_date: datetime,
        random_seed: Optional[int] = None
    ) -> Tuple[List[models.Sample], Dict[str, Any]]:
        """
        Select cut-off Test of Details sample.
        
        Selects approximately last 10 invoices before cutoff date
        and first 10-15 invoices after cutoff date.
        """
        snapshot = self.db.query(models.PopulationSnapshot).filter(
            models.PopulationSnapshot.id == snapshot_id
        ).first()
        
        if not snapshot:
            raise SamplingException(f"Snapshot {snapshot_id} not found")
        
        # Get transactions with valid dates
        transactions = self._get_transactions_with_dates(snapshot)
        
        if not transactions:
            raise SamplingException("No transactions with valid dates found")
        
        # Sort by date
        transactions.sort(key=lambda t: t.invoice_date)
        
        # Select pre-cutoff (last 10 before cutoff)
        pre_cutoff = [t for t in transactions if t.invoice_date < cutoff_date]
        pre_selected = pre_cutoff[-self.CUTOFF_PRE_COUNT:] if pre_cutoff else []
        
        # Select post-cutoff (first 10-15 after cutoff)
        post_cutoff = [t for t in transactions if t.invoice_date >= cutoff_date]
        post_count = min(
            len(post_cutoff),
            random.randint(self.CUTOFF_POST_COUNT_MIN, self.CUTOFF_POST_COUNT_MAX)
        )
        post_selected = post_cutoff[:post_count] if post_cutoff else []
        
        # Create samples
        samples = []
        order = 1
        
        for txn in pre_selected:
            sample = models.Sample(
                transaction_id=txn.id,
                selection_reasons=[SampleSelectionReason.CUTOFF_PRE],
                stratum="CUTOFF_PRE",
                selection_order=order
            )
            samples.append(sample)
            order += 1
        
        for txn in post_selected:
            sample = models.Sample(
                transaction_id=txn.id,
                selection_reasons=[SampleSelectionReason.CUTOFF_POST],
                stratum="CUTOFF_POST",
                selection_order=order
            )
            samples.append(sample)
            order += 1
        
        metadata = {
            "algorithm_version": self.ALGORITHM_VERSION,
            "cutoff_date": cutoff_date.isoformat(),
            "pre_cutoff_target": self.CUTOFF_PRE_COUNT,
            "pre_cutoff_actual": len(pre_selected),
            "post_cutoff_target_range": f"{self.CUTOFF_POST_COUNT_MIN}-{self.CUTOFF_POST_COUNT_MAX}",
            "post_cutoff_actual": len(post_selected),
            "total_selected": len(samples),
            "coverage_summary": f"Selected {len(pre_selected)} pre-cutoff and {len(post_selected)} post-cutoff transactions"
        }
        
        return samples, metadata
    
    def _get_eligible_transactions(
        self, snapshot: models.PopulationSnapshot
    ) -> List[models.Transaction]:
        """Get all eligible transactions from snapshot."""
        # Get transactions from source versions in snapshot
        source_version_ids = snapshot.source_version_ids or []
        
        transactions = self.db.query(models.Transaction).filter(
            models.Transaction.source_version_id.in_(source_version_ids),
            models.Transaction.engagement_id == snapshot.engagement_id
        ).all()
        
        return transactions
    
    def _get_transactions_with_dates(
        self, snapshot: models.PopulationSnapshot
    ) -> List[models.Transaction]:
        """Get transactions with valid invoice dates."""
        transactions = self._get_eligible_transactions(snapshot)
        return [t for t in transactions if t.invoice_date is not None]
    
    def _select_high_risk(
        self,
        transactions: List[models.Transaction],
        count: int
    ) -> List[Tuple[models.Transaction, List[str], Dict[str, Any]]]:
        """Select high-risk transactions."""
        # Sort by risk score (highest first)
        with_risk = [t for t in transactions if t.risk_score is not None]
        with_risk.sort(key=lambda t: t.risk_score, reverse=True)
        
        selected = []
        for txn in with_risk[:count]:
            selected.append((
                txn,
                [SampleSelectionReason.HIGH_RISK],
                {"risk_score": txn.risk_score}
            ))
        
        return selected
    
    def _select_related_party(
        self,
        transactions: List[models.Transaction],
        already_selected: List,
        min_count: int
    ) -> List[Tuple[models.Transaction, List[str], Dict[str, Any]]]:
        """Select related party transactions."""
        selected_ids = {txn.id for txn, _, _ in already_selected}
        
        related = [
            t for t in transactions
            if t.is_related_party and t.id not in selected_ids
        ]
        
        # Select up to min_count
        selected = []
        for txn in related[:min_count]:
            selected.append((
                txn,
                [SampleSelectionReason.RELATED_PARTY],
                {"related_party": True}
            ))
        
        return selected
    
    def _select_non_related_party(
        self,
        transactions: List[models.Transaction],
        already_selected: List,
        min_count: int
    ) -> List[Tuple[models.Transaction, List[str], Dict[str, Any]]]:
        """Select non-related party transactions."""
        selected_ids = {txn.id for txn, _, _ in already_selected}
        
        non_related = [
            t for t in transactions
            if not t.is_related_party and t.id not in selected_ids
        ]
        
        selected = []
        for txn in non_related[:min_count]:
            selected.append((
                txn,
                [SampleSelectionReason.NON_RELATED_PARTY],
                {"related_party": False}
            ))
        
        return selected
    
    def _select_high_value(
        self,
        transactions: List[models.Transaction],
        already_selected: List,
        count: int
    ) -> List[Tuple[models.Transaction, List[str], Dict[str, Any]]]:
        """Select high-value transactions."""
        selected_ids = {txn.id for txn, _, _ in already_selected}
        
        with_amount = [
            t for t in transactions
            if t.gross_amount is not None and t.id not in selected_ids
        ]
        with_amount.sort(key=lambda t: t.gross_amount, reverse=True)
        
        selected = []
        for txn in with_amount[:count]:
            selected.append((
                txn,
                [SampleSelectionReason.HIGH_VALUE],
                {"gross_amount": txn.gross_amount}
            ))
        
        return selected
    
    def _select_customer_diversity(
        self,
        transactions: List[models.Transaction],
        already_selected: List,
        min_customers: int
    ) -> List[Tuple[models.Transaction, List[str], Dict[str, Any]]]:
        """Ensure customer diversity in sample."""
        selected_ids = {txn.id for txn, _, _ in already_selected}
        selected_customers = {txn.customer_name for txn, _, _ in already_selected}
        
        # Get transactions from customers not yet selected
        available = [
            t for t in transactions
            if t.customer_name not in selected_customers and t.id not in selected_ids
        ]
        
        # Group by customer
        by_customer = {}
        for txn in available:
            if txn.customer_name not in by_customer:
                by_customer[txn.customer_name] = []
            by_customer[txn.customer_name].append(txn)
        
        # Select one transaction per new customer
        selected = []
        for customer, txns in list(by_customer.items())[:min_customers]:
            txn = txns[0]  # Pick first transaction for this customer
            selected.append((
                txn,
                [SampleSelectionReason.CUSTOMER_DIVERSITY],
                {"customer_name": customer}
            ))
        
        return selected
    
    def _random_fill(
        self,
        transactions: List[models.Transaction],
        already_selected: List,
        count: int
    ) -> List[Tuple[models.Transaction, List[str], Dict[str, Any]]]:
        """Random fill to reach target count."""
        selected_ids = {txn.id for txn, _, _ in already_selected}
        
        available = [t for t in transactions if t.id not in selected_ids]
        
        # Randomly select
        random.shuffle(available)
        selected = []
        
        for txn in available[:count]:
            selected.append((
                txn,
                [SampleSelectionReason.RANDOM_FILL],
                {}
            ))
        
        return selected
    
    def _generate_coverage_summary(
        self,
        metadata: Dict[str, Any],
        target: int,
        actual: int,
        shortfall: int
    ) -> str:
        """Generate human-readable coverage summary."""
        lines = [
            f"Target: {target} samples, Actual: {actual} samples",
            f"High risk: {metadata['high_risk_count']}",
            f"High value: {metadata['high_value_count']}",
            f"Related party: {metadata['related_party_count']}",
            f"Non-related party: {metadata['non_related_party_count']}",
            f"Customer diversity: {metadata['customer_diversity_count']}",
            f"Random fill: {metadata['random_fill_count']}"
        ]
        
        if shortfall > 0:
            lines.append(f"WARNING: Shortfall of {shortfall} samples due to insufficient population")
        
        return "\n".join(lines)
