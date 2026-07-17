import QtQuick 6.0
import QtQuick.Controls 6.0
import QtCore

ApplicationWindow  {
    id: window
    width: settings.width
    height: settings.height
    visible: true
    flags: Qt.FramelessWindowHint | Qt.Window
    color: "transparent"
    property string textColor: "white"
    property string nomebot: configData.botname

    Settings {
        id: settings

        property alias x : window.x
        property alias y : window.y
        property alias width : window.width
        property alias height : window.height
        onWidthChanged: {
            settings.width = window.width;
        }
        onHeightChanged: {
            settings.height = window.height;
        }
    }


    Timer {
        id: settingsCheckTimer
        interval: 1000 // intervallo in millisecondi (1 secondo)
        running: true
        repeat: true
        onTriggered: {
            // Avvio processo di controllo se il botname è attivo e relativo cambio di colore
            animationManager.checkColor()
        }
    }

    // Menu contestuale
    Menu {
       id: contextMenu

       MenuItem {
          text: "Layout singolo"
          onTriggered: animationManager.loadWindow()
       }


    }

    Rectangle {
        id: animazione
        width: parent.width
        height: parent.height
        color: "transparent"


        AnimatedImage {
            id: animation
            anchors.fill: parent
            anchors.margins: 10
            source: "breath_round.gif"
            //height: 100; width: 75
            fillMode: Image.PreserveAspectFit
            smooth: false
            cache: true

        }

        Text {
            objectName: "botname"
            id:botname
            font.family: "Space Age"
            anchors.fill: parent
            anchors.margins: 15
            font.bold: true
            font.pointSize: 50
            minimumPointSize: 5
            fontSizeMode: Text.Fit
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            color: textColor
            text: nomebot


        }

        Button { // attiva il menu di configurazione
                    id: configButton
                    width: 30
                    height: 30
                    anchors.top: animazione.top
                    anchors.right: parent.right
                    //anchors.margins: 10
                    icon.source: "settings.png"  // Assicurati che il percorso dell'icona sia corretto
                    flat: true  // Rende il button senza bordi, se lo desideri
                    background: Rectangle {
                        color: "transparent"  // Rende lo sfondo trasparente, se lo desideri
                    }


        }

    }

    MouseArea {
      anchors.fill: parent
      acceptedButtons: Qt.LeftButton | Qt.RightButton
      drag.target: parent
      property int edgeMargin: 10
      property bool moveMode: false

      onWheel: function(wheel) {
                let delta = wheel.angleDelta.y / 120; // 120 è il valore tipico per una rotazione del mouse wheel
                window.width += delta * 10; // Cambia la larghezza
                window.height += delta * 10; // Cambia l'altezza


                // Assicuriamoci che la finestra non diventi troppo piccola
                if (window.width < 100) window.width = 100;
                if (window.height < 75) window.height = 75;
            }
      onPressed: (mouse)=> {
          var mappedPoint = mapToItem(configButton, mouse.x,mouse.y);
          if (!moveMode && configButton.contains(mappedPoint)) {
                if (mouse.button == Qt.LeftButton) {
                    contextMenu.popup();
                }
                else {
                    mouse.accepted = false;
                    return;
                }
          }

          if (mouse.button == Qt.LeftButton)
                window.startSystemMove();
            else
             if (mouse.button == Qt.RightButton) {
                animationManager.stop_process()
                window.close();
           }
        }
     }



}

