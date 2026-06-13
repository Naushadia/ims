from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Computed, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.product import Product


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        Computed("quantity * unit_price", persisted=True),
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", lazy="joined")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_pos"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_price_nonneg"),
    )

    def __repr__(self) -> str:
        return f"<OrderItem order_id={self.order_id} product_id={self.product_id} qty={self.quantity}>"
