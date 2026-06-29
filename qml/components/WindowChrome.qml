import QtQuick
import QtQuick.Window

// Poignées de redimensionnement pour fenêtres frameless (startSystemResize).
Item {
    id: root
    required property Window window

    anchors.fill: parent
    z: 1000

    readonly property int grip: 6

    MouseArea {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.grip
        cursorShape: Qt.SizeHorCursor
        onPressed: window.startSystemResize(Qt.LeftEdge)
    }
    MouseArea {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.grip
        cursorShape: Qt.SizeHorCursor
        onPressed: window.startSystemResize(Qt.RightEdge)
    }
    MouseArea {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: root.grip
        cursorShape: Qt.SizeVerCursor
        onPressed: window.startSystemResize(Qt.TopEdge)
    }
    MouseArea {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: root.grip
        cursorShape: Qt.SizeVerCursor
        onPressed: window.startSystemResize(Qt.BottomEdge)
    }
    MouseArea {
        anchors.left: parent.left
        anchors.top: parent.top
        width: root.grip
        height: root.grip
        cursorShape: Qt.SizeFDiagCursor
        onPressed: window.startSystemResize(Qt.LeftEdge | Qt.TopEdge)
    }
    MouseArea {
        anchors.right: parent.right
        anchors.top: parent.top
        width: root.grip
        height: root.grip
        cursorShape: Qt.SizeBDiagCursor
        onPressed: window.startSystemResize(Qt.RightEdge | Qt.TopEdge)
    }
    MouseArea {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        width: root.grip
        height: root.grip
        cursorShape: Qt.SizeBDiagCursor
        onPressed: window.startSystemResize(Qt.LeftEdge | Qt.BottomEdge)
    }
    MouseArea {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: root.grip
        height: root.grip
        cursorShape: Qt.SizeFDiagCursor
        onPressed: window.startSystemResize(Qt.RightEdge | Qt.BottomEdge)
    }
}
