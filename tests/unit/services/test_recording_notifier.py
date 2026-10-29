from builders import taipei
from homewellness.models.alert_policy import EscalationAction
from homewellness.models.interaction import Notification, Recipient
from homewellness.services.notifier import RecordingNotifier


def note():
    return Notification("e1", EscalationAction.NOTIFY_FAMILY, "t", "b", (Recipient.FAMILY,),
                        taipei(8, 5))


def should_call_the_hook_after_a_notification_was_stored():
    seen = []
    notifier = RecordingNotifier(on_send=seen.append)
    notifier.send(note())
    assert seen == notifier.list_sent() == [note()]


def should_not_call_the_hook_when_the_send_fails():
    seen = []
    notifier = RecordingNotifier(on_send=seen.append)
    notifier.fail_next = True
    try:
        notifier.send(note())
    except RuntimeError:
        pass
    assert seen == []


def should_forget_all_notifications_when_it_is_cleared():
    notifier = RecordingNotifier()
    notifier.send(note())
    notifier.clear()
    assert notifier.list_sent() == []
