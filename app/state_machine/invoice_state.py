from enum import Enum
from typing import Set
from app.core.exceptions import InvalidStateTransitionError


class InvoiceState(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


TERMINAL_STATES: Set[InvoiceState] = {InvoiceState.PAID, InvoiceState.VOID}


class InvoiceStateMachine:
    """
    Formal State Machine for Invoice lifecycle management.
    Enforces transitions, invariants, and raises descriptive errors on invalid attempts.
    """

    VALID_TRANSITIONS = {
        InvoiceState.DRAFT: {InvoiceState.OPEN, InvoiceState.VOID},
        InvoiceState.OPEN: {InvoiceState.PAID, InvoiceState.VOID, InvoiceState.UNCOLLECTIBLE, InvoiceState.OPEN},
        InvoiceState.UNCOLLECTIBLE: {InvoiceState.OPEN, InvoiceState.VOID},
        InvoiceState.PAID: set(),  # Terminal
        InvoiceState.VOID: set(),  # Terminal
    }

    @classmethod
    def can_transition(cls, from_state: InvoiceState, to_state: InvoiceState) -> bool:
        allowed = cls.VALID_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    @classmethod
    def transition(cls, current_state_str: str, target_state: InvoiceState, action: str) -> InvoiceState:
        try:
            current = InvoiceState(current_state_str)
        except ValueError:
            raise InvalidStateTransitionError(
                current_state=current_state_str,
                action=action,
                reason=f"Unknown current state '{current_state_str}'"
            )

        if current in TERMINAL_STATES:
            raise InvalidStateTransitionError(
                current_state=current.value,
                action=action,
                reason=f"'{current.value}' is an immutable terminal state. No further transitions permitted."
            )

        if not cls.can_transition(current, target_state):
            allowed_str = ", ".join(f"'{s.value}'" for s in cls.VALID_TRANSITIONS.get(current, set()))
            raise InvalidStateTransitionError(
                current_state=current.value,
                action=action,
                reason=f"Transition to '{target_state.value}' is disallowed. Valid next states: [{allowed_str}]."
            )

        return target_state

    @classmethod
    def assert_can_pay(cls, current_state_str: str) -> None:
        try:
            current = InvoiceState(current_state_str)
        except ValueError:
            raise InvalidStateTransitionError(
                current_state=current_state_str,
                action="pay",
                reason=f"Unknown invoice state '{current_state_str}'"
            )

        if current == InvoiceState.PAID:
            raise InvalidStateTransitionError(
                current_state=current.value,
                action="pay",
                reason="Invoice has already been paid in full. Cannot process additional payments."
            )

        if current == InvoiceState.VOID:
            raise InvalidStateTransitionError(
                current_state=current.value,
                action="pay",
                reason="Invoice is void. Cannot process payments on voided invoices."
            )

        if current != InvoiceState.OPEN:
            raise InvalidStateTransitionError(
                current_state=current.value,
                action="pay",
                reason=f"Invoice must be in 'open' state to accept payments (current: '{current.value}')."
            )
