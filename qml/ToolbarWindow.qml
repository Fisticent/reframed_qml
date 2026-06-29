import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "components"

Window {
    id: bar
    transientParent: null
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window
    color: "transparent"
    width: frame.implicitWidth
    height: frame.implicitHeight
    opacity: 0.95
    visible: false

    x: app.getStr("toolbar_x") !== "" ? parseInt(app.getStr("toolbar_x")) : 100
    y: app.getStr("toolbar_y") !== "" ? parseInt(app.getStr("toolbar_y")) : 100

    property string classIcon: ""
    property bool showInv: app.getStr("overlay_show_inv") === "" ? true : app.getBool("overlay_show_inv")
    property bool showCarac: app.getStr("overlay_show_carac") === "" ? true : app.getBool("overlay_show_carac")
    property bool showSort: app.getStr("overlay_show_sort") === "" ? true : app.getBool("overlay_show_sort")
    property bool showHavre: app.getStr("overlay_show_havre") === "" ? true : app.getBool("overlay_show_havre")
    property bool showZaap: app.getStr("overlay_show_zaap") === "" ? true : app.getBool("overlay_show_zaap")
    property bool showInvite: app.getStr("overlay_show_invite") === "" ? true : app.getBool("overlay_show_invite")

    function refreshFlags() {
        showInv = app.getStr("overlay_show_inv") === "" ? true : app.getBool("overlay_show_inv")
        showCarac = app.getStr("overlay_show_carac") === "" ? true : app.getBool("overlay_show_carac")
        showSort = app.getStr("overlay_show_sort") === "" ? true : app.getBool("overlay_show_sort")
        showHavre = app.getStr("overlay_show_havre") === "" ? true : app.getBool("overlay_show_havre")
        showZaap = app.getStr("overlay_show_zaap") === "" ? true : app.getBool("overlay_show_zaap")
        showInvite = app.getStr("overlay_show_invite") === "" ? true : app.getBool("overlay_show_invite")
    }

    Connections {
        target: app
        function onClassDisplayChanged(className) { bar.classIcon = app.skinUrl(className) }
        function onTogglesChanged() { bar.refreshFlags() }
    }

    component MacroButton: Button {
        id: ctl
        property string iconSource: ""
        property string fallback: ""
        property string tip: ""
        property color baseColor: Colors.secondary
        property color hoverColor: Colors.primary_hover
        implicitWidth: 32
        implicitHeight: 32
        hoverEnabled: true
        focusPolicy: Qt.StrongFocus

        ToolTip.visible: hovered && tip !== "" && app.showTooltips
        ToolTip.text: tip
        ToolTip.delay: 400

        background: Rectangle {
            radius: Colors.radius_control
            color: ctl.hovered ? ctl.hoverColor : ctl.baseColor
            border.width: ctl.activeFocus ? 2 : 0
            border.color: Colors.focus_ring
            scale: ctl.pressed ? 0.98 : 1.0
        }

        contentItem: Item {
            Image {
                anchors.centerIn: parent
                width: 20; height: 20
                sourceSize.width: 20; sourceSize.height: 20
                source: ctl.iconSource
                visible: ctl.iconSource !== ""
            }
            Text {
                anchors.centerIn: parent
                text: ctl.fallback
                visible: ctl.iconSource === ""
                color: Colors.text
                font.bold: true
                font.pixelSize: Colors.font_size_ui
            }
        }
    }

    Rectangle {
        id: frame
        anchors.fill: parent
        implicitWidth: col.implicitWidth + 10
        implicitHeight: col.implicitHeight + 10
        color: Colors.bg
        radius: Colors.radius_control
        border.width: 1
        border.color: Colors.secondary

        ColumnLayout {
            id: col
            spacing: 4
            anchors.centerIn: parent

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 18
                color: Colors.toolbar_header
                radius: 4
                Text {
                    anchors.centerIn: parent
                    text: "≡ Reframed ≡"
                    color: Colors.text
                    font.pixelSize: 9
                    font.bold: true
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.SizeAllCursor
                    onPressed: bar.startSystemMove()
                    onReleased: {
                        app.saveValue("toolbar_x", Math.round(bar.x))
                        app.saveValue("toolbar_y", Math.round(bar.y))
                    }
                }
            }

            RowLayout {
                spacing: 3
                MacroButton {
                    iconSource: app.assetUrl("icons/open-panel.svg")
                    fallback: "UI"
                    tip: "Ouvrir l'interface principale"
                    baseColor: Colors.secondary
                    hoverColor: Colors.secondary_hover
                    onClicked: app.showWindow()
                }
                ThemedComboBox {
                    id: modeCombo
                    implicitWidth: 80
                    implicitHeight: 30
                    model: ["ALL", "Team 1", "Team 2"]
                    currentIndex: Math.max(0, model.indexOf(app.currentMode))
                    onActivated: app.setMode(currentText)
                    Connections {
                        target: app
                        function onCurrentModeChanged() {
                            modeCombo.currentIndex = Math.max(0, modeCombo.model.indexOf(app.currentMode))
                        }
                    }
                }
                Item { Layout.fillWidth: true; implicitWidth: 4 }
                MacroButton {
                    fallback: "F5"; tip: "Rafraîchir les pages Dofus"
                    baseColor: Colors.secondary; hoverColor: Colors.secondary_hover
                    onClicked: app.refresh()
                }
                MacroButton {
                    iconSource: app.skinUrl("dupliquer"); fallback: "📋"
                    tip: "Coller + Entrée sur toutes les pages"
                    baseColor: Colors.primary_button; hoverColor: Colors.primary_button_hover
                    onClicked: app.pasteEnter()
                }
            }

            RowLayout {
                spacing: 3
                Rectangle {
                    width: 32; height: 32; radius: Colors.radius_control
                    color: Colors.secondary_hover
                    Image {
                        anchors.centerIn: parent
                        width: 24; height: 24
                        source: bar.classIcon
                        visible: bar.classIcon !== ""
                        sourceSize.width: 24; sourceSize.height: 24
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "?"
                        color: Colors.text
                        visible: bar.classIcon === ""
                    }
                }
                MacroButton {
                    visible: bar.showInv
                    iconSource: app.assetUrl("skin/inventaire.png"); fallback: "I"
                    tip: "Ouvrir Inventaire"
                    onClicked: app.broadcastKey("game_inv_key", "i")
                }
                MacroButton {
                    visible: bar.showCarac
                    iconSource: app.assetUrl("skin/carac.png"); fallback: "C"
                    tip: "Ouvrir Caractéristiques"
                    onClicked: app.broadcastKey("game_char_key", "c")
                }
                MacroButton {
                    visible: bar.showSort
                    iconSource: app.assetUrl("skin/sort.png"); fallback: "S"
                    tip: "Ouvrir Sorts"
                    onClicked: app.broadcastKey("game_spell_key", "s")
                }
                MacroButton {
                    visible: bar.showHavre
                    iconSource: app.assetUrl("skin/havresac.png"); fallback: "H"
                    tip: "Ouvrir Havre-Sac"
                    onClicked: app.broadcastKey("game_haven_key", "h")
                }
                MacroButton {
                    visible: bar.showZaap
                    iconSource: app.assetUrl("skin/zaap.png"); fallback: "Z"
                    tip: "Auto-Zaap"
                    onClicked: app.autoZaap()
                }
                MacroButton {
                    visible: bar.showInvite
                    iconSource: app.assetUrl("skin/invite.png"); fallback: "G"
                    tip: "Invitation de Groupe"
                    onClicked: app.groupInvite()
                }
            }
        }
    }
}
