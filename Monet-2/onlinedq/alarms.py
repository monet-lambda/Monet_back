from onlinedq import online # https://gitlab.cern.ch/lhcb-dq/online-dq
from onlinedq.online import get_histogram_object

class MonetAlarms(object):
    @property
    def _hdb(self):
        self._tmp_hdb = OnlineHistDB()
        return self._tmp_hdb._hdb

    def get_message_ids(self):
        ret = []
        return ret

    def get_list_of_alarms(self):
        message_ids = self.get_message_ids()
        return [self.get_alarm(m) for m in message_ids]

    def get_alarm(self, msg_id):
        ret = {
            "id": msg_id,
            "system": msg.concernedSystem(),
            "is_abort": msg.isAbort(),
            "is_active": msg.isactive(),
            "text": msg.msgtext(),
            "level": msg.levelString(),
            "file": msg.saveSet(),
            "histogram_id": msg.hIdentifier()
        }
        return ret
