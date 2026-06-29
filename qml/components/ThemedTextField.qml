import QtQuick
import QtQuick.Controls.Basic

TextField {
    id: control
    implicitHeight: 30
    color: Colors.text
    selectionColor: Colors.primary_button
    selectedTextColor: Colors.text_on_accent
    placeholderTextColor: Colors.text_muted
    font.pixelSize: 12

    background: Rectangle {
        color: control.enabled ? Colors.bg_elevated : Colors.secondary_dark
        border.color: control.activeFocus ? Colors.focus_ring
                    : (control.hovered ? Colors.secondary_hover : Colors.secondary)
        border.width: control.activeFocus ? 2 : 1
        radius: 6
    }
}
