# Messages

## MSG-1 Manager owns the PO channel
roles: manager
topic: messages

The Manager alone talks to the PO and relays every question that needs a PO answer.

## MSG-2a Manager reports to the Team Lead
roles: manager
when: size = S
topic: messages

The Manager sends the Tech Lead every answer to a status question.

## MSG-2b Manager reports through the Team Lead
roles: manager
when: size in M, L
topic: messages

The Manager sends the Team Lead every answer to a status question.
