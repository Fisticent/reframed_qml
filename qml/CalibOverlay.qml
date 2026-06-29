import QtQuick
import QtQuick.Window

Window {
    id: overlay
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
           | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus
    color: "transparent"
    visible: false

    property string message: ""

    width: 560
    height: banner.implicitHeight + 24
    // bandeau centré horizontalement, près du haut de l'écran
    x: Screen.virtualX + (Screen.width - width) / 2
    y: Screen.virtualY + 40

    function showText(text) {
        overlay.message = text
        overlay.show()
        overlay.raise()
    }

    Rectangle {
        id: banner
        anchors.centerIn: parent
        width: parent.width - 24
        implicitHeight: txt.implicitHeight + 24
        radius: 10
        color: Colors.bg_card
        border.color: Colors.calib_border
        border.width: 2
        opacity: 0.97

        Text {
            id: txt
            anchors.fill: parent
            anchors.margins: 12
            text: overlay.message
            color: Colors.text
            font.pixelSize: 14
            font.bold: true
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    Connections {
        target: app
        function onCalibInstruction(text) { overlay.showText(text) }
        function onCalibInstructionHide() { overlay.hide() }
    }
}
