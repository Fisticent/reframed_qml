import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "ThemeUtils.js" as Theme

Item {
    id: root
    property string configKey: ""
    property string labelText: ""
    property string tooltipText: ""
    property bool compact: false

    property bool waiting: false
    readonly property string keyValue: app.hotkeys[configKey] || ""

    implicitWidth: compact ? 76 : (labelItem.implicitWidth + keyBtn.implicitWidth + clearBtn.implicitWidth + 8)
    implicitHeight: compact ? 40 : 30
    Layout.fillWidth: compact
    Layout.preferredWidth: compact ? 76 : implicitWidth

  // ---- mode étendu (Paramètres) ----
    RowLayout {
        visible: !root.compact
        anchors.fill: parent
        spacing: 4

        Label {
            id: labelItem
            text: labelText + ":"
            color: Colors.text
            font.pixelSize: Colors.font_size_ui
            Layout.minimumWidth: 70
        }

        Button {
            id: keyBtn
            Layout.preferredWidth: 88
            Layout.preferredHeight: 30
            hoverEnabled: true
            focusPolicy: Qt.StrongFocus
            text: root.waiting ? "..." : (root.keyValue ? root.keyValue : "Aucun")
            readonly property color fillColor: root.waiting ? Colors.warning
                : (root.keyValue ? (keyBtn.hovered ? Colors.primary_button_hover : Colors.primary_button)
                                 : (keyBtn.hovered ? Colors.secondary_hover : Colors.secondary))
            ToolTip.visible: hovered && root.tooltipText !== "" && app.showTooltips
            ToolTip.text: root.tooltipText
            ToolTip.delay: 400
            contentItem: Text {
                text: keyBtn.text
                color: root.keyValue || root.waiting
                       ? Theme.textForFill(keyBtn.fillColor, Colors)
                       : Colors.text_muted
                font.pixelSize: Colors.font_size_ui
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            background: Rectangle {
                radius: Colors.radius_control
                color: keyBtn.fillColor
                border.width: keyBtn.activeFocus ? 2 : 0
                border.color: Colors.focus_ring
                scale: keyBtn.pressed ? 0.98 : 1.0
            }
            onClicked: { root.waiting = true; app.catchKey(configKey, true) }
        }

        Button {
            id: clearBtn
            Layout.preferredWidth: 28
            Layout.preferredHeight: 30
            hoverEnabled: true
            focusPolicy: Qt.StrongFocus
            text: "✕"
            ToolTip.visible: hovered && app.showTooltips
            ToolTip.text: "Effacer le raccourci"
            ToolTip.delay: 400
            contentItem: Text {
                text: "✕"
                color: Colors.text_muted
                font.pixelSize: Colors.font_size_ui
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                radius: Colors.radius_control
                color: parent.hovered ? Colors.danger : "transparent"
                border.width: parent.activeFocus ? 2 : 0
                border.color: Colors.focus_ring
                scale: parent.pressed ? 0.98 : 1.0
            }
            onClicked: app.clearKey(configKey)
        }
    }

  // ---- mode compact (fenêtre principale) ----
    ColumnLayout {
        visible: root.compact
        width: 76
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        spacing: 2

        Text {
            text: root.labelText
            color: Colors.text_muted
            font.pixelSize: 9
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        RowLayout {
            spacing: 2
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter

            Button {
                id: keyBtnCompact
                Layout.preferredWidth: 54
                Layout.preferredHeight: 24
                hoverEnabled: true
                focusPolicy: Qt.StrongFocus
                text: root.waiting ? "…" : (root.keyValue ? root.keyValue : "—")
                readonly property color fillColor: root.waiting ? Colors.warning
                    : (root.keyValue ? (keyBtnCompact.hovered ? Colors.primary_button_hover : Colors.primary_button)
                                     : (keyBtnCompact.hovered ? Colors.secondary_hover : Colors.secondary))
                ToolTip.visible: hovered && root.tooltipText !== "" && app.showTooltips
                ToolTip.text: root.tooltipText
                ToolTip.delay: 400
                contentItem: Text {
                    text: keyBtnCompact.text
                    color: root.keyValue || root.waiting
                           ? Theme.textForFill(keyBtnCompact.fillColor, Colors)
                           : Colors.text_muted
                    font.pixelSize: 10
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                background: Rectangle {
                    radius: 4
                    color: keyBtnCompact.fillColor
                    border.width: keyBtnCompact.activeFocus ? 2 : 0
                    border.color: Colors.focus_ring
                    scale: keyBtnCompact.pressed ? 0.98 : 1.0
                }
                onClicked: { root.waiting = true; app.catchKey(configKey, true) }
            }

            Button {
                Layout.preferredWidth: 18
                Layout.preferredHeight: 24
                hoverEnabled: true
                focusPolicy: Qt.StrongFocus
                text: "✕"
                ToolTip.visible: hovered && app.showTooltips
                ToolTip.text: "Effacer"
                ToolTip.delay: 400
                contentItem: Text {
                    text: "✕"
                    color: Colors.text_muted
                    font.pixelSize: 9
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 4
                    color: parent.hovered ? Colors.danger : "transparent"
                    border.width: parent.activeFocus ? 2 : 0
                    border.color: Colors.focus_ring
                }
                onClicked: app.clearKey(configKey)
            }
        }
    }

    Connections {
        target: app
        function onHotkeysChanged() { root.waiting = false }
        function onListeningChanged() { if (!app.isListening) root.waiting = false }
    }
}
