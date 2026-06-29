import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "components"

Window {
    id: win
    width: 620
    height: 680
    title: "⚙️ Gestionnaire de Binds Avancé REFRAMED"
    flags: Qt.Window | Qt.WindowStaysOnTopHint
    color: Colors.bg
    visible: false

    property string mode: "cycle"
    property string modifier: "ctrl"

    function openManager() {
        reload()
        win.show(); win.raise(); win.requestActivate()
    }

    function reload() {
        var data = app.getBindManagerData()
        win.mode = data.mode
        win.modifier = data.modifier
        rowsModel.clear()
        for (var i = 0; i < data.rows.length; i++) {
            var r = data.rows[i]
            rowsModel.append({ "rid": r.id, "label": r.label, "sub": r.sub, "key": r.key, "icon": r.icon })
        }
    }

    ListModel { id: rowsModel }

    Connections {
        target: app
        function onBindKeyCaptured(rowId, key) {
            for (var i = 0; i < rowsModel.count; i++) {
                if (rowsModel.get(i).rid === rowId) { rowsModel.setProperty(i, "key", key); break }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 12

        // header
        Rectangle {
            Layout.fillWidth: true; color: Colors.bg_card; radius: 8
            implicitHeight: headerCol.implicitHeight + 24
            ColumnLayout {
                id: headerCol
                anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                anchors.margins: 12; spacing: 10
                RowLayout {
                    Label { text: "Mode :"; color: Colors.text; font.bold: true; Layout.minimumWidth: 110 }
                    Row {
                        spacing: 4
                        Repeater {
                            model: ["cycle", "bind"]
                            ThemedButton {
                                required property string modelData
                                text: modelData
                                implicitWidth: 90
                                baseColor: win.mode === modelData ? Colors.primary : Colors.secondary
                                hoverColor: win.mode === modelData ? Colors.primary_hover : Colors.secondary_hover
                                onClicked: { win.mode = modelData; app.setBindMode(modelData); win.reload() }
                            }
                        }
                    }
                }
                RowLayout {
                    Label { text: "Préfixe global :"; color: Colors.text; font.bold: true; Layout.minimumWidth: 110 }
                    Row {
                        spacing: 4
                        Repeater {
                            model: ["aucun", "ctrl", "alt", "shift"]
                            ThemedButton {
                                required property string modelData
                                text: modelData
                                implicitWidth: 70
                                baseColor: win.modifier === modelData ? Colors.primary : Colors.secondary
                                hoverColor: win.modifier === modelData ? Colors.primary_hover : Colors.secondary_hover
                                onClicked: win.modifier = modelData
                            }
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            color: Colors.text_muted
            font.italic: true
            wrapMode: Text.WordWrap
            text: win.mode === "cycle"
                  ? "Cible fixe par place (ex. : la ligne 1 cible le 1er de l'initiative)."
                  : "Cible fixe par pseudo (même si l'ordre change)."
        }

        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true
            contentWidth: availableWidth
            clip: true
            ColumnLayout {
                width: win.width - 50
                spacing: 4
                Repeater {
                    model: rowsModel
                    Rectangle {
                        required property int index
                        required property var model
                        Layout.fillWidth: true
                        color: Colors.bg_card; radius: 8
                        implicitHeight: 52
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 15; anchors.rightMargin: 15
                            Image {
                                visible: model.icon !== ""
                                source: model.icon
                                width: 28; height: 28
                                sourceSize.width: 28; sourceSize.height: 28
                            }
                            Text { text: model.label; color: Colors.text; font.bold: true; font.pixelSize: 15 }
                            Text { text: model.sub; color: Colors.text_muted; font.italic: true }
                            Item { Layout.fillWidth: true }
                            ThemedButton {
                                text: model.key ? model.key.toUpperCase() : "Aucun"
                                implicitWidth: 80
                                baseColor: Colors.secondary; hoverColor: Colors.secondary_hover
                                onClicked: app.catchBindKey(model.rid)
                            }
                            ThemedButton {
                                text: "✕"; implicitWidth: 26
                                baseColor: Colors.danger; hoverColor: Colors.danger_hover
                                onClicked: rowsModel.setProperty(index, "key", "")
                            }
                        }
                    }
                }
            }
        }

        ThemedButton {
            Layout.alignment: Qt.AlignHCenter
            text: "💾 Enregistrer les raccourcis"; implicitWidth: 240
            baseColor: Colors.success; hoverColor: Colors.primary_bright
            onClicked: {
                var out = []
                for (var i = 0; i < rowsModel.count; i++) {
                    var r = rowsModel.get(i)
                    out.push({ "id": r.rid, "key": r.key })
                }
                app.saveBindManager(win.modifier, out)
                win.close()
            }
        }
    }
}
