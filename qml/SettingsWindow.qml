import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "components"

Window {
    id: win
    width: 540
    height: 720
    minimumWidth: 360
    minimumHeight: 320
    title: "⚙️ Paramètres REFRAMED"
    flags: Qt.Window | Qt.WindowStaysOnTopHint
    color: Colors.bg
    visible: false

    function openSettings() { win.show(); win.raise(); win.requestActivate() }

    component SectionTitle: Text {
        color: Colors.text
        font.pixelSize: Colors.font_size_heading
        font.bold: true
        Layout.topMargin: 12
        Layout.alignment: Qt.AlignHCenter
    }

    ScrollView {
        anchors.fill: parent
        anchors.margins: 8
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: win.width - 32
            spacing: 8

            SectionTitle { text: "Raccourcis Jeu & Macros" }
            Rectangle {
                Layout.fillWidth: true
                color: Colors.bg_card
                radius: Colors.radius_card
                implicitHeight: gameGrid.implicitHeight + 24
                GridLayout {
                    id: gameGrid
                    anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                    anchors.margins: 12
                    columns: 2
                    rowSpacing: 8; columnSpacing: 20
                    HotkeyButton { configKey: "game_inv_key"; labelText: "Inventaire"; tooltipText: "Touche jeu pour ouvrir l'inventaire" }
                    HotkeyButton { configKey: "game_char_key"; labelText: "Carac"; tooltipText: "Touche jeu pour les caractéristiques" }
                    HotkeyButton { configKey: "game_spell_key"; labelText: "Sorts"; tooltipText: "Touche jeu pour les sorts" }
                    HotkeyButton { configKey: "game_haven_key"; labelText: "Havre-Sac"; tooltipText: "Touche jeu pour le Havre-Sac" }
                    Rectangle { Layout.columnSpan: 2; Layout.fillWidth: true; height: 2; color: Colors.secondary }
                    HotkeyButton { configKey: "invite_group_key"; labelText: "Inviter Groupe"; tooltipText: "Inviter automatiquement le groupe" }
                    HotkeyButton { configKey: "auto_zaap_key"; labelText: "Auto-Zaap"; tooltipText: "Lancer la macro Auto-Zaap" }
                    HotkeyButton { configKey: "paste_enter_key"; labelText: "Ctrl+V/Entrée"; tooltipText: "Coller et Entrée sur tout le monde" }
                    HotkeyButton { configKey: "refresh_key"; labelText: "Actualiser"; tooltipText: "Actualisation des pages" }
                    HotkeyButton { configKey: "sort_taskbar_key"; labelText: "Trier Barre"; tooltipText: "Trie la barre des tâches Windows" }
                    HotkeyButton { configKey: "calib_key"; labelText: "Calibrage"; tooltipText: "Touche de bind calibrage" }
                }
            }

            SectionTitle { text: "Roue de Focus (Radiale)" }
            Rectangle {
                Layout.fillWidth: true
                color: Colors.bg_card
                radius: Colors.radius_card
                implicitHeight: radialCol.implicitHeight + 24
                ColumnLayout {
                    id: radialCol
                    anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 8
                    ThemedSwitch {
                        text: "Activer la roue"
                        checked: app.radialActive
                        tooltipText: "Activer ou désactiver la roue de sélection"
                        onToggled: app.saveBool("radial_menu_active", checked)
                    }
                    HotkeyButton { configKey: "radial_menu_hotkey"; labelText: "Raccourci"; tooltipText: "Touche/clic qui ouvre la roue" }
                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "Volume roulette :"; color: Colors.text }
                        ThemedSlider {
                            id: volSlider
                            Layout.fillWidth: true
                            Layout.preferredWidth: 180
                            from: 0; to: 100
                            value: app.volumeLevel
                            onMoved: app.setVolume(Math.round(value))
                        }
                        Text {
                            text: Math.round(volSlider.value) + "%"
                            color: Colors.text_muted
                            font.pixelSize: Colors.font_size_ui
                            Layout.minimumWidth: 36
                        }
                    }
                }
            }

            SectionTitle { text: "Vitesse du Clic Multi" }
            Rectangle {
                Layout.fillWidth: true
                color: Colors.bg_card
                radius: Colors.radius_card
                implicitHeight: 56
                RowLayout {
                    anchors.fill: parent; anchors.margins: 12
                    Label { text: "Vitesse :"; color: Colors.text }
                    ThemedComboBox {
                        id: speedCombo
                        model: ["Rapide", "Moyen", "Lent"]
                        currentIndex: Math.max(0, model.indexOf(app.getStr("click_speed")))
                        onActivated: app.saveString("click_speed", currentText)
                    }
                    Item { Layout.fillWidth: true }
                }
            }

            SectionTitle { text: "Macro Auto-Zaap" }
            Rectangle {
                Layout.fillWidth: true
                color: Colors.bg_card
                radius: Colors.radius_card
                implicitHeight: 56
                RowLayout {
                    anchors.fill: parent; anchors.margins: 12
                    Label { text: "Délai avant clic (sec) :"; color: Colors.text }
                    ThemedTextField {
                        id: zaapDelay
                        Layout.preferredWidth: 70
                        text: app.getStr("zaap_delay")
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        validator: DoubleValidator { bottom: 0; top: 30; decimals: 2 }
                        onEditingFinished: app.saveString("zaap_delay", text)
                    }
                    Item { Layout.fillWidth: true }
                }
            }

            SectionTitle { text: "Personnalisation de l'Overlay" }
            Rectangle {
                Layout.fillWidth: true
                color: Colors.bg_card
                radius: Colors.radius_card
                implicitHeight: ovGrid.implicitHeight + 24
                GridLayout {
                    id: ovGrid
                    anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                    anchors.margins: 12
                    columns: 3; rowSpacing: 6; columnSpacing: 10
                    ThemedSwitch { text: "Inventaire"; checked: app.getStr("overlay_show_inv")==="" ? true : app.getBool("overlay_show_inv"); onToggled: app.saveBool("overlay_show_inv", checked) }
                    ThemedSwitch { text: "Carac."; checked: app.getStr("overlay_show_carac")==="" ? true : app.getBool("overlay_show_carac"); onToggled: app.saveBool("overlay_show_carac", checked) }
                    ThemedSwitch { text: "Sorts"; checked: app.getStr("overlay_show_sort")==="" ? true : app.getBool("overlay_show_sort"); onToggled: app.saveBool("overlay_show_sort", checked) }
                    ThemedSwitch { text: "Havre-Sac"; checked: app.getStr("overlay_show_havre")==="" ? true : app.getBool("overlay_show_havre"); onToggled: app.saveBool("overlay_show_havre", checked) }
                    ThemedSwitch { text: "Auto-Zaap"; checked: app.getStr("overlay_show_zaap")==="" ? true : app.getBool("overlay_show_zaap"); onToggled: app.saveBool("overlay_show_zaap", checked) }
                    ThemedSwitch { text: "Groupe"; checked: app.getStr("overlay_show_invite")==="" ? true : app.getBool("overlay_show_invite"); onToggled: app.saveBool("overlay_show_invite", checked) }
                }
            }

            SectionTitle { text: "Zone sensible" }
            Rectangle {
                Layout.fillWidth: true
                color: Colors.bg_card
                radius: Colors.radius_card
                border.color: Colors.danger
                border.width: 1
                implicitHeight: 56
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    Text {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        color: Colors.text_muted
                        font.pixelSize: Colors.font_size_ui
                        text: "Remet tous les paramètres à zéro."
                    }
                    ThemedButton {
                        text: "Réinitialiser"
                        baseColor: Colors.danger
                        hoverColor: Colors.danger_hover
                        tooltipText: "Remise à zéro de tous les paramètres"
                        onClicked: app.resetSettings()
                    }
                }
            }

            ThemedButton {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 12; Layout.bottomMargin: 16
                text: "Fermer & Sauvegarder"; implicitWidth: 200
                baseColor: Colors.success; hoverColor: Colors.success_hover
                onClicked: { app.saveString("zaap_delay", zaapDelay.text); win.close() }
            }
        }
    }
}
