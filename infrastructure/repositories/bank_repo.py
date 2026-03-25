"""银行仓储"""
from typing import Optional, List
from sqlalchemy.orm import Session
import time

from ..database.schema import BankAccountTable, LoanTable, BankTransactionTable
from ...domain.models.bank import BankAccount, Loan, BankTransaction


class BankRepository:
    """银行仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    # ===== 银行账户相关 =====
    
    def get_bank_account(self, user_id: str) -> Optional[BankAccount]:
        """获取银行账户"""
        row = self.session.query(BankAccountTable).filter(
            BankAccountTable.user_id == user_id
        ).first()
        
        if not row:
            return None
        
        return BankAccount(
            user_id=row.user_id,
            balance=row.balance,
            last_interest_time=row.last_interest_time
        )
    
    def create_or_update_bank_account(self, user_id: str, balance: int, last_interest_time: int):
        """创建或更新银行账户"""
        row = self.session.query(BankAccountTable).filter(
            BankAccountTable.user_id == user_id
        ).first()
        
        if row:
            row.balance = balance
            row.last_interest_time = last_interest_time
        else:
            row = BankAccountTable(
                user_id=user_id,
                balance=balance,
                last_interest_time=last_interest_time
            )
            self.session.add(row)
        
        self.session.commit()
    
    # ===== 贷款相关 =====
    
    def get_active_loan(self, user_id: str) -> Optional[Loan]:
        """获取进行中的贷款"""
        row = self.session.query(LoanTable).filter(
            LoanTable.user_id == user_id,
            LoanTable.status == 1
        ).first()
        
        if not row:
            return None
        
        return self._loan_to_domain(row)
    
    def create_loan(self, user_id: str, principal: int, interest_rate: float,
                    borrowed_at: int, due_at: int, loan_type: str) -> int:
        """创建贷款"""
        row = LoanTable(
            user_id=user_id,
            principal=principal,
            interest_rate=interest_rate,
            borrowed_at=borrowed_at,
            due_at=due_at,
            loan_type=loan_type,
            status=1
        )
        
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        
        return row.id
    
    def close_loan(self, loan_id: int):
        """关闭贷款（还清）"""
        self.session.query(LoanTable).filter(
            LoanTable.id == loan_id
        ).update({
            "status": 2
        })
        self.session.commit()
    
    def mark_loan_overdue(self, loan_id: int):
        """标记贷款逾期"""
        self.session.query(LoanTable).filter(
            LoanTable.id == loan_id
        ).update({
            "status": 3
        })
        self.session.commit()
    
    def get_overdue_loans(self, current_time: int) -> List[Loan]:
        """获取所有逾期贷款"""
        rows = self.session.query(LoanTable).filter(
            LoanTable.status == 1,
            LoanTable.due_at < current_time
        ).all()
        
        return [self._loan_to_domain(row) for row in rows]
    
    # ===== 交易记录相关 =====
    
    def add_transaction(self, user_id: str, trans_type: str, amount: int,
                       balance_after: int, description: str, created_at: int):
        """添加交易记录"""
        row = BankTransactionTable(
            user_id=user_id,
            trans_type=trans_type,
            amount=amount,
            balance_after=balance_after,
            description=description,
            created_at=created_at
        )
        
        self.session.add(row)
        self.session.commit()
    
    def get_transactions(self, user_id: str, limit: int = 20) -> List[BankTransaction]:
        """获取交易记录"""
        rows = self.session.query(BankTransactionTable).filter(
            BankTransactionTable.user_id == user_id
        ).order_by(BankTransactionTable.created_at.desc()).limit(limit).all()
        
        return [self._transaction_to_domain(row) for row in rows]
    
    # ===== 排行榜相关 =====
    
    def get_deposit_ranking(self, limit: int = 10) -> List[dict]:
        """获取存款排行榜"""
        rows = self.session.query(BankAccountTable).order_by(
            BankAccountTable.balance.desc()
        ).limit(limit).all()
        
        return [
            {
                "user_id": row.user_id,
                "balance": row.balance
            }
            for row in rows
        ]
    
    # ===== 辅助方法 =====
    
    def _loan_to_domain(self, row: LoanTable) -> Loan:
        """转换为领域模型"""
        return Loan(
            id=row.id,
            user_id=row.user_id,
            principal=row.principal,
            interest_rate=row.interest_rate,
            borrowed_at=row.borrowed_at,
            due_at=row.due_at,
            loan_type=row.loan_type,
            status=row.status
        )
    
    def _transaction_to_domain(self, row: BankTransactionTable) -> BankTransaction:
        """转换为领域模型"""
        return BankTransaction(
            id=row.id,
            user_id=row.user_id,
            trans_type=row.trans_type,
            amount=row.amount,
            balance_after=row.balance_after,
            description=row.description,
            created_at=row.created_at
        )
