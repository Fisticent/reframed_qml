import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "components"

Window {
    id: win
    width: 560
    height: 520
    minimumWidth: 480
    minimumHeight: 440
    title: "Tutoriel Reframed"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"
    visible: false

    readonly property bool motion: !(typeof Qt !== "undefined" && Qt.styleHints && Qt.styleHints.reduceAnimations)

    property int page: 0
    property int slideDir: 1
    property int pendingPage: 0
    property bool transitioning: false

    readonly property int pageCount: 6

    function fmt(key) {
        var v = app.hotkeys[key] || ""
        return v ? v.toUpperCase() : "—"
    }

    function pageIcon(idx) {
        switch (idx) {
        case 0: return "icons/tutorial-welcome.svg"
        case 1: return "icons/shortcuts.svg"
        case 2: return "icons/teams.svg"
        case 3: return "icons/calibrations.svg"
        case 4: return "icons/overlay-bar.svg"
        case 5: return "icons/radial.svg"
        default: return "icons/tutorial-welcome.svg"
        }
    }

    function pageTitle(idx) {
        switch (idx) {
        case 0: return "Bienvenue"
        case 1: return "Raccourcis"
        case 2: return "Équipes & chef"
        case 3: return "Calibrages"
        case 4: return "Overlay"
        case 5: return "Roue & Paramètres"
        default: return ""
        }
    }

    function pageBody(idx) {
        switch (idx) {
        case 0:
            return "Reframed pilote le multi-compte Dofus sur Windows.\n\n"
                 + "1. Lance Dofus, puis clique Rafraîchir.\n"
                 + "2. Active les comptes dans la liste.\n"
                 + "3. Calibre une fois (section Calibrages).\n\n"
                 + "Ce guide reprend l'essentiel en 1 minute."
        case 1:
            return "• " + fmt("prev_key") + " / " + fmt("next_key") + " : personnage précédent / suivant.\n"
                 + "• " + fmt("leader_key") + " : focus sur le chef.\n"
                 + "• " + fmt("toggle_app_key") + " : masquer / afficher l'interface.\n"
                 + "• " + fmt("sync_key") + " / " + fmt("sync_right_key") + " : clics synchronisés.\n"
                 + "• " + fmt("swap_xp_drop_key") + " : swap XP/Drop.\n\n"
                 + "Modifiables dans la carte Raccourcis."
        case 2:
            return "• Contrôler (header) : ALL, Team 1 ou Team 2.\n"
                 + "• T1 / T2 sur chaque ligne : changer l'équipe.\n"
                 + "• Étoile : définir le chef de l'équipe.\n"
                 + "• Flèches : réordonner les comptes.\n\n"
                 + "Le chef est repris après chaque action multi si « Focus chef » est actif."
        case 3:
            return "Calibre une fois par poste — l'état reste visible en chips :\n\n"
                 + "• Chat : zone de saisie du chat.\n"
                 + "• XP/Drop : boutons d'attribution.\n"
                 + "• Havre-Sac : icône du sac.\n"
                 + "• Invitation : bouton d'invitation.\n\n"
                 + "Clique un chip gris pour lancer le calibrage guidé."
        case 4:
            return "• Overlay : barre flottante en jeu (toggle dans Options rapides).\n"
                 + "• Cacher l'UI : masque la fenêtre principale, l'overlay reste.\n"
                 + "• Inviter groupe / Fermer team : actions du jour.\n\n"
                 + "L'overlay reste accessible même quand Reframed est réduit."
        case 5:
            return "• Roue radiale : " + fmt("radial_menu_hotkey") + " (configurable).\n"
                 + "  Maintenir la touche, survoler un perso, relâcher.\n"
                 + "• Paramètres : touches jeu, zaap, volume roue, reset.\n\n"
                 + "Tu peux rouvrir ce tutoriel via le bouton Tuto."
        default:
            return ""
        }
    }

    function openTutorial() {
        page = 0
        slideDir = 1
        skipFuture.checked = false
        content.opacity = 1
        content.x = 0
        iconBadge.scale = 1
        win.show()
        win.raise()
        win.requestActivate()
    }

    function finishTutorial() {
        if (skipFuture.checked)
            app.markTutorialDone()
        win.close()
    }

    function goToPage(target) {
        if (transitioning || target === page || target < 0 || target >= pageCount)
            return
        slideDir = target > page ? 1 : -1
        pendingPage = target
        if (!motion) {
            page = target
            return
        }
        transitioning = true
        pageExit.start()
    }

    SequentialAnimation {
        id: pageExit
        ParallelAnimation {
            NumberAnimation { target: content; property: "opacity"; to: 0; duration: 140; easing.type: Easing.OutQuad }
            NumberAnimation { target: content; property: "x"; to: -28 * win.slideDir; duration: 180; easing.type: Easing.InQuad }
        }
        ScriptAction {
            script: {
                win.page = win.pendingPage
                content.x = 28 * win.slideDir
                iconPulse.start()
            }
        }
        ParallelAnimation {
            NumberAnimation { target: content; property: "opacity"; to: 1; duration: 200; easing.type: Easing.OutCubic }
            NumberAnimation { target: content; property: "x"; to: 0; duration: 220; easing.type: Easing.OutCubic }
        }
        ScriptAction { script: win.transitioning = false }
    }

    SequentialAnimation {
        id: iconPulse
        NumberAnimation { target: iconBadge; property: "scale"; to: 0.82; duration: 80 }
        NumberAnimation { target: iconBadge; property: "scale"; to: 1.06; duration: 140; easing.type: Easing.OutBack }
        NumberAnimation { target: iconBadge; property: "scale"; to: 1; duration: 100 }
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

        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 2
            color: Colors.primary_bright
            width: parent.width * (win.page + 1) / win.pageCount
            Behavior on width {
                enabled: win.motion
                NumberAnimation { duration: 280; easing.type: Easing.OutCubic }
            }
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                color: Colors.bg_elevated
                topLeftRadius: Colors.radius_window
                topRightRadius: Colors.radius_window

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 8
                    Text {
                        text: "Tutoriel"
                        color: Colors.text
                        font.pixelSize: Colors.font_size_heading
                        font.bold: true
                    }
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.SizeAllCursor
                            onPressed: win.startSystemMove()
                        }
                    }
                    ThemedButton {
                        text: "×"
                        implicitWidth: 30
                        implicitHeight: 28
                        labelOnFill: false
                        textColor: Colors.danger
                        baseColor: Colors.secondary_dark
                        hoverColor: Colors.danger_hover
                        tooltipText: "Fermer"
                        onClicked: win.finishTutorial()
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 20

                ColumnLayout {
                    id: content
                    anchors.fill: parent
                    spacing: 14

                    Item {
                        Layout.alignment: Qt.AlignHCenter
                        width: 56
                        height: 56

                        Rectangle {
                            anchors.centerIn: parent
                            width: 56
                            height: 56
                            radius: 28
                            color: Colors.bg_elevated
                            border.width: 1
                            border.color: Colors.secondary
                            opacity: iconGlow.opacity
                        }

                        Rectangle {
                            id: iconGlow
                            anchors.centerIn: parent
                            width: 56
                            height: 56
                            radius: 28
                            color: Colors.primary_bright
                            opacity: 0.12
                            SequentialAnimation on opacity {
                                running: win.visible && win.motion
                                loops: Animation.Infinite
                                NumberAnimation { to: 0.22; duration: 1400; easing.type: Easing.InOutSine }
                                NumberAnimation { to: 0.08; duration: 1400; easing.type: Easing.InOutSine }
                            }
                        }

                        Item {
                            id: iconBadge
                            anchors.centerIn: parent
                            width: 28
                            height: 28
                            Image {
                                anchors.centerIn: parent
                                source: app.assetUrl(win.pageIcon(win.page))
                                width: 28
                                height: 28
                                sourceSize.width: 28
                                sourceSize.height: 28
                            }
                        }
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: win.pageTitle(win.page)
                        color: Colors.primary_bright
                        font.pixelSize: 22
                        font.bold: true
                    }

                    Text {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: win.pageBody(win.page)
                        color: Colors.text
                        font.pixelSize: Colors.font_size_ui + 1
                        lineHeight: 1.45
                        wrapMode: Text.WordWrap
                    }

                    Row {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 6
                        Repeater {
                            model: win.pageCount
                            Rectangle {
                                required property int index
                                width: index === win.page ? 20 : 6
                                height: 6
                                radius: 3
                                color: index === win.page ? Colors.primary_bright : Colors.secondary
                                Behavior on width {
                                    enabled: win.motion
                                    NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
                                }
                                Behavior on color {
                                    enabled: win.motion
                                    ColorAnimation { duration: 180 }
                                }
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 16
                Layout.rightMargin: 16
                Layout.bottomMargin: 14
                spacing: 8

                ThemedCheckBox {
                    id: skipFuture
                    text: "Ne plus afficher au démarrage"
                }

                Item { Layout.fillWidth: true }

                ThemedButton {
                    text: "Passer"
                    implicitWidth: 76
                    implicitHeight: 30
                    baseColor: Colors.secondary_dark
                    hoverColor: Colors.secondary
                    onClicked: win.finishTutorial()
                }
                ThemedButton {
                    text: "Préc."
                    implicitWidth: 64
                    implicitHeight: 30
                    enabled: win.page > 0 && !win.transitioning
                    baseColor: Colors.secondary
                    hoverColor: Colors.secondary_hover
                    onClicked: win.goToPage(win.page - 1)
                }
                ThemedButton {
                    text: win.page === win.pageCount - 1 ? "Terminer" : "Suiv."
                    implicitWidth: 88
                    implicitHeight: 30
                    enabled: !win.transitioning
                    baseColor: win.page === win.pageCount - 1 ? Colors.success : Colors.primary_button
                    hoverColor: win.page === win.pageCount - 1 ? Colors.success_hover : Colors.primary_button_hover
                    onClicked: {
                        if (win.page < win.pageCount - 1)
                            win.goToPage(win.page + 1)
                        else
                            win.finishTutorial()
                    }
                }
            }
        }
    }
}
