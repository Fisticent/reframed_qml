import QtQuick
import QtQuick.Controls.Basic

ComboBox {
    id: control
    implicitHeight: 30

    contentItem: Text {
        leftPadding: 10
        rightPadding: control.indicator.width + 8
        text: control.displayText
        color: control.enabled ? Colors.text : Colors.text_muted
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        color: control.enabled ? Colors.bg_elevated : Colors.secondary_dark
        border.color: control.activeFocus ? Colors.focus_ring
                    : (control.hovered ? Colors.secondary_hover : Colors.secondary)
        border.width: control.activeFocus ? 2 : 1
        radius: 6
    }

    indicator: Text {
        x: control.width - width - 8
        y: (control.height - height) / 2
        text: "▾"
        color: Colors.text_muted
        font.pixelSize: 10
    }

    popup: Popup {
        y: control.height + 2
        width: control.width
        padding: 4
        implicitHeight: contentItem.implicitHeight + padding * 2

        contentItem: ListView {
            clip: true
            implicitHeight: Math.min(contentHeight, 240)
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            color: Colors.bg_card
            border.color: Colors.secondary_hover
            border.width: 1
            radius: 6
        }
    }

    delegate: ItemDelegate {
        width: control.width - 8
        height: 28
        highlighted: control.highlightedIndex === index

        contentItem: Text {
            text: control.textRole ? model[control.textRole] : modelData
            color: highlighted ? Colors.text : Colors.text
            font.pixelSize: 12
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }

        background: Rectangle {
            color: highlighted || hovered ? Colors.secondary_hover : "transparent"
            radius: 4
        }
    }
}
