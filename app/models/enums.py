import enum     


print("enums.py loaded ✅")


class UserRole(str, enum.Enum):
    OFFICER = "OFFICER"
    SUPERVISOR = "SUPERVISOR"
    OPERATOR = "OPERATOR"

print("UserRole in scope?", 'UserRole' in globals())
print("Available globals:", list(globals().keys()))

class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RECEIVED = "RECEIVED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"

class SessionEndReason(str, enum.Enum):
    LOGOUT = "LOGOUT"
    EXPIRED = "EXPIRED"