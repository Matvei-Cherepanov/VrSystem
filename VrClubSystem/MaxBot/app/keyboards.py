from maxapi.types import MessageButton, ButtonsPayload

main = ButtonsPayload(buttons=
[
    [
        MessageButton(text="Забронировать место")
    ],
]).pack()

type_choice = ButtonsPayload(buttons=
[
    [
        MessageButton(text="Одиночное место"),
    ],
    [
        MessageButton(text="Компания")
    ],
]).pack()

success = ButtonsPayload(buttons=
[
    [
        MessageButton(text="Всё верно"),
        MessageButton(text="Отмена")
    ],
]).pack()