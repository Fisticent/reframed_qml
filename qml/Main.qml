import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: mainWin
    width: Math.min(700, Screen.desktopAvailableWidth - 40)
    height: Math.min(880, Screen.desktopAvailableHeight - 60)
    minimumWidth: 560
    minimumHeight: 480
    maximumWidth: Screen.desktopAvailableWidth
    maximumHeight: Screen.desktopAvailableHeight
    title: "Reframed"
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    visible: true

    property string activeName: ""
    readonly property bool narrowLayout: mainWin.width < 600

    // ---- fenêtres secondaires ----
    SettingsWindow   { id: settingsWin; objectName: "settingsWin" }
    TutorialWindow   { id: tutoWin; objectName: "tutoWin" }
    CharManagerWindow { id: charWin; objectName: "charWin" }
    ToolbarWindow    { id: toolbarWin; objectName: "toolbarWin" }
    RadialMenu       { id: radialWin; objectName: "radialWin" }
    CalibOverlay     { id: calibOverlay; objectName: "calibOverlay" }

    function syncToolbarVisibility() {
        if (app.toolbarActive)
            toolbarWin.show()
        else
            toolbarWin.hide()
    }

    Component.onCompleted: {
        syncToolbarVisibility()
        var sx = app.getStr("window_x")
        var sy = app.getStr("window_y")
        if (sx !== "" && sy !== "") {
            mainWin.x = parseInt(sx)
            mainWin.y = parseInt(sy)
        }
    }

    function saveGeometry() {
        app.saveValue("window_x", Math.round(mainWin.x))
        app.saveValue("window_y", Math.round(mainWin.y))
    }
    Timer {
        id: geomTimer; interval: 400; repeat: false
        onTriggered: mainWin.saveGeometry()
    }
    onXChanged: if (mainWin.visible) geomTimer.restart()
    onYChanged: if (mainWin.visible) geomTimer.restart()

    onWindowStateChanged: function(state) {
        if (state === Qt.WindowMinimized)
            toolbarPersistTimer.restart()
        else
            syncToolbarVisibility()
    }
    onVisibilityChanged: syncToolbarVisibility()

    Timer {
        id: toolbarPersistTimer
        interval: 80
        repeat: false
        onTriggered: syncToolbarVisibility()
    }

    onClosing: function(close) {
        close.accepted = false
        saveGeometry()
        app.hideWindow()
    }

    // ---- réactions aux signaux backend ----
    Connections {
        target: app
        function onRequestShowMain() { mainWin.show(); mainWin.raise(); mainWin.requestActivate() }
        function onRequestHideMain() { mainWin.saveGeometry(); mainWin.hide(); mainWin.syncToolbarVisibility() }
        function onRequestToggleMain() { mainWin.visible ? mainWin.hide() : (mainWin.show(), mainWin.raise(), mainWin.requestActivate()) }
        function onRequestQuit() { Qt.quit() }
        function onLaunchTutorialRequested() { tutoWin.openTutorial() }
        function onConflictDetected() { conflictDialog.open() }
        function onHotkeyCaptured(key, value) { app.applyHotkey(key, value) }
        function onActiveHighlightChanged(name) { mainWin.activeName = name }
    }

    WindowChrome {
        anchors.fill: parent
        window: mainWin
    }

    Rectangle {
        id: shell
        anchors.fill: parent
        radius: Colors.radius_window
        color: Colors.bg
        clip: true
        antialiasing: true
        border.width: 1
        border.color: Colors.secondary

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // ---------- BARRE TITRE (fixe, coins haut arrondis) ----------
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                color: Colors.bg_elevated
                topLeftRadius: Colors.radius_window
                topRightRadius: Colors.radius_window
                clip: true

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 8
                    spacing: 6

                    Item {
                        Layout.preferredWidth: titleRow.implicitWidth
                        Layout.fillHeight: true

                        RowLayout {
                            id: titleRow
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 8
                            Image {
                                source: app.assetUrl("logo_transparent.png")
                                width: 22; height: 22
                                sourceSize.width: 22; sourceSize.height: 22
                                visible: source != ""
                            }
                            Text {
                                text: "Reframed"
                                color: Colors.text
                                font.pixelSize: Colors.font_size_title
                                font.bold: true
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.SizeAllCursor
                            onPressed: mainWin.startSystemMove()
                        }
                    }

                    RowLayout {
                        spacing: 4
                        Label {
                            text: "Contrôler"
                            visible: !mainWin.narrowLayout
                            color: Colors.text_muted
                            font.pixelSize: 11
                        }
                        ThemedComboBox {
                            id: modeCombo
                            implicitWidth: mainWin.narrowLayout ? 88 : 110
                            implicitHeight: 28
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
                    }

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.SizeAllCursor
                            onPressed: mainWin.startSystemMove()
                        }
                    }

                    ThemedButton {
                        text: "Tuto"
                        implicitWidth: 52
                        implicitHeight: 28
                        baseColor: Colors.primary_button
                        hoverColor: Colors.primary_button_hover
                        tooltipText: "Découvrir toutes les fonctionnalités"
                        onClicked: app.launchTutorial()
                    }
                    ThemedButton {
                        text: "Paramètres"
                        implicitWidth: 88
                        implicitHeight: 28
                        baseColor: Colors.secondary
                        hoverColor: Colors.secondary_hover
                        tooltipText: "Paramètres du jeu et de la roue"
                        onClicked: settingsWin.openSettings()
                    }
                    ThemedButton {
                        text: "Cacher l'UI"
                        implicitWidth: 82
                        implicitHeight: 28
                        baseColor: Colors.secondary_dark
                        hoverColor: Colors.secondary
                        borderW: 1
                        borderColor: Colors.secondary_hover
                        tooltipText: "Masquer dans la barre des tâches"
                        onClicked: app.hideWindow()
                    }
                    ThemedButton {
                        text: "—"
                        implicitWidth: 30
                        implicitHeight: 28
                        baseColor: Colors.secondary_dark
                        hoverColor: Colors.secondary
                        tooltipText: "Réduire"
                        onClicked: mainWin.showMinimized()
                    }
                    ThemedButton {
                        text: "×"
                        implicitWidth: 30
                        implicitHeight: 28
                        labelOnFill: false
                        textColor: Colors.danger
                        baseColor: Colors.secondary_dark
                        hoverColor: Colors.danger_hover
                        tooltipText: "Quitter REFRAMED complètement"
                        onClicked: app.hardKill()
                    }
                }
            }

    // ===================================================================
    //  Contenu principal (scrollable)
    // ===================================================================
    ScrollView {
        id: mainScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: mainScroll.availableWidth
            spacing: 8

            // ---------- PILOTAGE : raccourcis + options ----------
            ColumnLayout {
                visible: mainWin.narrowLayout
                Layout.fillWidth: true
                Layout.topMargin: 8
                Layout.leftMargin: 15; Layout.rightMargin: 15
                spacing: 8
                PilotageShortcutsCard { Layout.fillWidth: true }
                OptionsCard { Layout.fillWidth: true }
            }

            RowLayout {
                visible: !mainWin.narrowLayout
                Layout.fillWidth: true
                Layout.topMargin: 8
                Layout.leftMargin: 15; Layout.rightMargin: 15
                spacing: 8
                PilotageShortcutsCard { Layout.fillWidth: true; Layout.alignment: Qt.AlignTop }
                OptionsCard { Layout.preferredWidth: 200; Layout.alignment: Qt.AlignTop }
            }

            // ---------- CALIBRAGES (état visible) ----------
            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 15; Layout.rightMargin: 15
                color: Colors.bg_card
                radius: Colors.radius_card
                implicitHeight: calibRow.implicitHeight + 24
                ColumnLayout {
                    id: calibRow
                    anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Image {
                            source: app.assetUrl("icons/calibrations.svg")
                            width: 15
                            height: 15
                            sourceSize.width: 15
                            sourceSize.height: 15
                        }
                        Text {
                            text: "Calibrages"
                            color: Colors.text
                            font.pixelSize: Colors.font_size_heading
                            font.bold: true
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "À faire une fois — l'état reste visible ici."
                        color: Colors.text_muted
                        font.pixelSize: 10
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        CalibChip { Layout.fillWidth: true; calibKey: "chat"; label: "Chat"; onTriggered: app.startCalibChat() }
                        CalibChip { Layout.fillWidth: true; calibKey: "xp"; label: "XP/Drop"; onTriggered: app.startCalibXpDrop() }
                        CalibChip { Layout.fillWidth: true; calibKey: "zaap"; label: "Havre-Sac"; onTriggered: app.startCalibZaap() }
                        CalibChip { Layout.fillWidth: true; calibKey: "invite"; label: "Invitation"; onTriggered: app.startCalibGroupAccept() }
                    }
                }
            }

            // ---------- ACTIONS COURANTES ----------
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 15; Layout.rightMargin: 15
                spacing: 8
                ThemedButton {
                    Layout.fillWidth: true
                    text: "Inviter groupe"
                    baseColor: Colors.primary_button
                    hoverColor: Colors.primary_button_hover
                    tooltipText: "Auto-invitation de l'équipe via le chat"
                    onClicked: app.groupInvite()
                }
                ThemedButton {
                    Layout.fillWidth: true
                    text: "Fermer team"
                    baseColor: Colors.danger
                    hoverColor: Colors.danger_hover
                    tooltipText: "Ferme toutes les fenêtres Dofus actives"
                    onClicked: app.closeAllAccounts()
                }
            }

            // ---------- COMPTES ACTIFS ----------
            Rectangle {
                Layout.fillWidth: true
                Layout.leftMargin: 15; Layout.rightMargin: 15
                color: Colors.bg_card; radius: 8
                implicitHeight: accountsCol.implicitHeight + 20
                ColumnLayout {
                    id: accountsCol
                    anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                    anchors.margins: 10; spacing: 6
                    RowLayout {
                        Layout.fillWidth: true
                        Rectangle {
                            Layout.fillWidth: true; implicitHeight: 32
                            color: Colors.bg_elevated; radius: 8
                            RowLayout {
                                anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 6
                                Text { text: "Comptes actifs"; color: Colors.text; font.pixelSize: 13 }
                                Item { Layout.fillWidth: true }
                                ThemedButton {
                                    text: "⚙️"; implicitWidth: 28; implicitHeight: 28
                                    baseColor: Colors.secondary_hover; hoverColor: Colors.secondary_dark
                                    tooltipText: "Gérer les raccourcis avancés par personnage"
                                    onClicked: charWin.openManager()
                                }
                            }
                        }
                    }
                    // liste
                    Text {
                        visible: app.accounts.length === 0
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                        color: Colors.text_muted
                        text: "Aucun compte détecté.\nLance Dofus puis clique « Rafraîchir » (ou F5)."
                        Layout.topMargin: 20; Layout.bottomMargin: 20
                    }
                    Repeater {
                        model: app.accounts
                        Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            radius: 6
                            implicitHeight: 38
                            color: modelData.name === mainWin.activeName ? Colors.radial_active : "transparent"
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 6; anchors.rightMargin: 6
                                spacing: 4
                                Image {
                                    source: modelData.icon
                                    visible: modelData.icon !== ""
                                    width: 24; height: 24; sourceSize.width: 24; sourceSize.height: 24
                                }
                                Text { visible: modelData.icon === ""; text: "👤"; color: Colors.text }
                                ThemedCheckBox {
                                    checked: modelData.active
                                    text: modelData.name.substring(0, 20)
                                    onToggled: app.toggleAccount(modelData.name, checked)
                                }
                                Item { Layout.fillWidth: true }
                                ThemedComboBox {
                                    implicitWidth: 56; implicitHeight: 30
                                    model: {
                                        var arr = []
                                        for (var i = 1; i <= modelData.count; i++) arr.push(String(i))
                                        return arr
                                    }
                                    currentIndex: modelData.pos - 1
                                    onActivated: app.changePosition(modelData.name, parseInt(currentText))
                                }
                                ThemedButton {
                                    implicitWidth: 30; implicitHeight: 30
                                    iconSource: app.assetUrl("icons/chevron-up.svg")
                                    baseColor: Colors.secondary
                                    tooltipText: "Monter"
                                    onClicked: app.moveRow(modelData.name, -1)
                                }
                                ThemedButton {
                                    implicitWidth: 30; implicitHeight: 30
                                    iconSource: app.assetUrl("icons/chevron-down.svg")
                                    baseColor: Colors.secondary
                                    tooltipText: "Descendre"
                                    onClicked: app.moveRow(modelData.name, 1)
                                }
                                ThemedButton {
                                    text: modelData.team === "Team 1" ? "T1" : "T2"; implicitWidth: 36; implicitHeight: 30
                                    baseColor: modelData.team === "Team 1" ? Colors.team1 : Colors.team2
                                    hoverColor: modelData.team === "Team 1" ? Colors.team1_hover : Colors.team2_hover
                                    tooltipText: "Changer l'équipe"
                                    onClicked: app.changeTeam(modelData.name)
                                }
                                ThemedButton {
                                    implicitWidth: 30; implicitHeight: 30
                                    iconSource: app.assetUrl(modelData.isLeader ? "icons/star-filled.svg" : "icons/star-outline.svg")
                                    baseColor: modelData.isLeader ? Colors.leader : "transparent"
                                    borderW: modelData.isLeader ? 0 : 1
                                    borderColor: Colors.secondary
                                    tooltipText: "Définir comme Chef"
                                    onClicked: app.setLeader(modelData.name)
                                }
                                ThemedButton {
                                    text: "✖"; implicitWidth: 30; implicitHeight: 30
                                    baseColor: Colors.danger; hoverColor: Colors.danger_hover
                                    tooltipText: "Fermer la fenêtre"
                                    onClicked: app.closeAccount(modelData.name)
                                }
                            }
                        }
                    }
                }
            }

            // ---------- FEEDBACK ----------
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: app.feedbackText
                color: app.feedbackColor
                font.pixelSize: 13; font.bold: true
                Layout.preferredHeight: 18
            }

            // ---------- FOOTER ----------
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 15; Layout.rightMargin: 15; Layout.bottomMargin: 16
                ThemedButton {
                    text: "Rafraîchir"; implicitWidth: 90
                    baseColor: Colors.secondary; hoverColor: Colors.secondary_hover
                    tooltipText: "Actualiser la liste des comptes"
                    onClicked: app.refresh()
                }
                ThemedButton {
                    text: "Trier Barre Windows"; implicitWidth: 150
                    baseColor: Colors.primary; hoverColor: Colors.primary_hover
                    tooltipText: "Organise les fenêtres dans la barre des tâches"
                    onClicked: app.sortTaskbar()
                }
                ThemedCheckBox {
                    id: tipChk
                    checked: app.showTooltips
                    text: "Infobulles"
                    onToggled: app.saveBool("show_tooltips", checked)
                }
            }
        }
    }
        }

    // ===================================================================
    //  Cartes pilotage réutilisables
    // ===================================================================
    component PilotageShortcutsCard: Rectangle {
        color: Colors.bg_card
        radius: Colors.radius_card
        implicitHeight: pilotBody.implicitHeight + 24

        ColumnLayout {
            id: pilotBody
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 10
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                Image {
                    source: app.assetUrl("icons/shortcuts.svg")
                    width: 15
                    height: 15
                    sourceSize.width: 15
                    sourceSize.height: 15
                }
                Text {
                    text: "Raccourcis"
                    color: Colors.text
                    font.pixelSize: Colors.font_size_heading
                    font.bold: true
                }
            }

            Text {
                Layout.fillWidth: true
                text: "Touches jeu & roue → ⚙️ Paramètres"
                color: Colors.text_muted
                font.pixelSize: 9
            }

            GridLayout {
                columns: mainWin.narrowLayout ? 2 : 4
                uniformCellWidths: true
                rowSpacing: 6
                columnSpacing: 6
                Layout.fillWidth: true

                HotkeyButton { compact: true; configKey: "prev_key"; labelText: "Préc."; tooltipText: "Focus perso précédent" }
                HotkeyButton { compact: true; configKey: "next_key"; labelText: "Suiv."; tooltipText: "Focus perso suivant" }
                HotkeyButton { compact: true; configKey: "leader_key"; labelText: "Chef"; tooltipText: "Reprendre focus sur le Chef" }
                HotkeyButton { compact: true; configKey: "toggle_app_key"; labelText: "UI"; tooltipText: "Masquer/Afficher l'app" }
                HotkeyButton { compact: true; configKey: "sync_key"; labelText: "Clic G."; tooltipText: "Clic gauche synchronisé" }
                HotkeyButton { compact: true; configKey: "sync_right_key"; labelText: "Clic D."; tooltipText: "Clic droit synchronisé" }
                HotkeyButton { compact: true; configKey: "swap_xp_drop_key"; labelText: "Swap"; tooltipText: "Clic synchro (XP/Drop)" }
            }
        }
    }

    component OptionsCard: Rectangle {
        color: Colors.bg_card
        radius: Colors.radius_card
        implicitHeight: optBody.implicitHeight + 24

        ColumnLayout {
            id: optBody
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 12
            spacing: 6

            Text {
                text: "Options rapides"
                color: Colors.text
                font.pixelSize: Colors.font_size_heading
                font.bold: true
            }

            ThemedSwitch {
                text: "Overlay"
                checked: app.toolbarActive
                tooltipText: "Barre de macros flottante en jeu"
                onToggled: { app.saveBool("toolbar_active", checked); mainWin.syncToolbarVisibility() }
            }
            ThemedSwitch {
                text: "Focus chef"
                checked: app.returnToLeader
                tooltipText: "Retour auto sur le chef après une action multi"
                onToggled: app.saveBool("return_to_leader", checked)
            }
            ThemedSwitch {
                text: "Spam clic"
                checked: app.spamClick
                tooltipText: "Maintenir la molette pour spammer les doubles clics"
                onToggled: app.saveBool("spam_click_active", checked)
            }
            ThemedSwitch {
                text: "Auto-invite"
                checked: app.autoInvite
                tooltipText: "Accepter auto les invitations de groupe"
                onToggled: { app.saveBool("auto_group_accept", checked); app.onAutoGroupAcceptChange() }
            }
            ThemedSwitch {
                text: "Auto-échange"
                checked: app.autoTrade
                tooltipText: "Accepter auto les demandes d'échange"
                onToggled: { app.saveBool("auto_accept_trade", checked); app.onAutoTradeChange() }
            }
        }
    }
    }

    // ===================================================================
    //  Dialog conflit Organizer
    // ===================================================================
    Dialog {
        id: conflictDialog
        anchors.centerIn: parent
        modal: true
        title: "⚠️ Conflit de logiciels détecté"
        width: 460
        property alias ignoreFuture: ignoreChk.checked
        background: Rectangle { color: Colors.bg_card; radius: Colors.radius_card; border.color: Colors.warning; border.width: 1 }
        contentItem: ColumnLayout {
            spacing: 12
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                color: Colors.text
                text: "Le logiciel 'Organizer' est actuellement ouvert.\nL'utilisation de deux gestionnaires simultanément\ncrée des bugs et des conflits de focus sur REFRAMED.\n\nNous vous recommandons fortement de le fermer."
            }
            ThemedCheckBox {
                id: ignoreChk
                text: "Ne plus m'afficher cet avertissement"
            }
            RowLayout {
                Layout.fillWidth: true
                ThemedButton {
                    Layout.fillWidth: true; text: "Fermer Organizer"
                    baseColor: Colors.danger; hoverColor: Colors.danger_hover
                    onClicked: { app.resolveConflictClose(ignoreChk.checked); conflictDialog.close() }
                }
                ThemedButton {
                    Layout.fillWidth: true; text: "Conserver"
                    baseColor: Colors.secondary; hoverColor: Colors.secondary_hover
                    onClicked: { app.resolveConflictKeep(ignoreChk.checked); conflictDialog.close() }
                }
            }
        }
    }
}
