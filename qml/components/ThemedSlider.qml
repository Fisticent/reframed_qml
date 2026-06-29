import QtQuick
import QtQuick.Controls.Basic

Slider {
    id: control
    implicitHeight: 28

    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        width: control.availableWidth
        height: 4
        radius: 2
        color: Colors.secondary

        Rectangle {
            width: control.visualPosition * parent.width
            height: parent.height
            radius: 2
            color: Colors.primary_button
        }
    }

    handle: Rectangle {
        x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
        y: control.topPadding + (control.availableHeight - height) / 2
        width: 16
        height: 16
        radius: 8
        color: control.pressed ? Colors.primary_button_hover : Colors.primary_button
        border.color: control.activeFocus ? Colors.focus_ring : Colors.primary_button_hover
        border.width: control.activeFocus ? 2 : 1
    }
}
