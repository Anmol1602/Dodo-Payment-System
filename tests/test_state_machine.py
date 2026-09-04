import pytest
from app.state_machine.invoice_state import InvoiceStateMachine, InvoiceState
from app.core.exceptions import InvalidStateTransitionError


def test_valid_transitions():
    assert InvoiceStateMachine.transition("draft", InvoiceState.OPEN, "finalize") == InvoiceState.OPEN
    assert InvoiceStateMachine.transition("draft", InvoiceState.VOID, "void") == InvoiceState.VOID
    assert InvoiceStateMachine.transition("open", InvoiceState.PAID, "pay") == InvoiceState.PAID
    assert InvoiceStateMachine.transition("open", InvoiceState.VOID, "void") == InvoiceState.VOID
    assert InvoiceStateMachine.transition("open", InvoiceState.UNCOLLECTIBLE, "mark_uncollectible") == InvoiceState.UNCOLLECTIBLE
    assert InvoiceStateMachine.transition("uncollectible", InvoiceState.OPEN, "reopen") == InvoiceState.OPEN


def test_terminal_paid_state_immutability():
    # Paid is terminal: attempting any transition must raise InvalidStateTransitionError
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        InvoiceStateMachine.transition("paid", InvoiceState.OPEN, "reopen")
    assert "immutable terminal state" in exc_info.value.message

    with pytest.raises(InvalidStateTransitionError):
        InvoiceStateMachine.transition("paid", InvoiceState.VOID, "void")


def test_terminal_void_state_immutability():
    # Void is terminal: attempting any transition must raise InvalidStateTransitionError
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        InvoiceStateMachine.transition("void", InvoiceState.OPEN, "reopen")
    assert "immutable terminal state" in exc_info.value.message


def test_assert_can_pay_invariants():
    # Only OPEN can be paid
    InvoiceStateMachine.assert_can_pay("open")

    with pytest.raises(InvalidStateTransitionError):
        InvoiceStateMachine.assert_can_pay("draft")

    with pytest.raises(InvalidStateTransitionError):
        InvoiceStateMachine.assert_can_pay("paid")

    with pytest.raises(InvalidStateTransitionError):
        InvoiceStateMachine.assert_can_pay("void")
