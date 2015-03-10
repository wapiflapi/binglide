
`VERSION` = BXMDP00


> When receiving messages a ROUTER socket shall prepend a message part
> containing the identity of the originating peer to the message before passing
> it to the application. When sending messages a ROUTER socket shall remove the
> first part of the message and use it to determine the identity of the peer the
> message shall be routed to.

This extra frame is not shown in the sub-protocol commands explained below.


## LIST

### from CLIENT

1. `VERSION`.LIST

### to CLIENT

1. `VERSION`.LIST
2. connected services (repeated)

## REQUEST

### from CLIENT

1. `VERSION`.REQUEST
2. service name; SHOULD be utf8 encoded string.
3. request id; opaque binary
4. client id, should be empty if not set by broker
5. request body; opaque binary

### to WORKER

1. `VERSION`.XREQUEST
2. return address; envelope stack
3. request id; opaque binary
4. client id, should be empty if not set by broker
5. request body; opaque binary


## CANCEL

### from CLIENT

1. `VERSION`.CANCEL
2. service name; SHOULD be utf8 encoded string. CAN be empty.
3. request id; opaque binary
4. client id, should be empty if not set by broker
5. request body; opaque binary

### to WORKER

1. `VERSION`.XCANCEL
2. return address; envelope stack
3. request id; opaque binary
4. client id, should be empty if not set by broker
5. request body; opaque binary


## REPORT

### from WORKER

1. `VERSION`.XREPORT
2. return address; envelope stack
3. request id; opaque binary4
4. client id, should be empty if not set by broker
5. report body; opaque binary

### to CLIENT

1. `VERSION`.REPORT
3. service name; SHOULD be utf8 encoded string.
2. request id; opaque binary
4. client id, should be empty if not set by broker
5. report body; opaque binary


## READY

### from WORKER

1. `VERSION`.READY
2. service name; SHOULD be utf8 encoded string.


## DISCONNECT

### to BROKER & from BROKER

1. `VERSION`.DISCONNECT

