// VariantPopup.qml
// Popup window for displaying apparatus criticus variants

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Window {
    id: variantPopup
    title: qsTr("Apparatus Criticus Variant")
    width: 600
    height: 400
    modality: Qt.ApplicationModal
    visible: false

    property var variantData: null

    function showVariant(variant) {
        variantData = variant
        variantPopup.open()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // Header with variant information
        GroupBox {
            title: qsTr("Variant Details")
            Layout.fillWidth: true

            GridLayout {
                columns: 2
                width: parent.width

                Label {
                    text: qsTr("Sigla:")
                    font.bold: true
                }
                Label {
                    text: variantData ? variantData.sigla || qsTr("Unknown") : ""
                    Layout.fillWidth: true
                }

                Label {
                    text: qsTr("Type:")
                    font.bold: true
                }
                Label {
                    text: variantData ? variantData.type || qsTr("variant") : ""
                    Layout.fillWidth: true
                }

                Label {
                    text: qsTr("Manuscript:")
                    font.bold: true
                }
                Label {
                    text: variantData ? getManuscriptName(variantData.sigla) : ""
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                }

                Label {
                    text: qsTr("Page:")
                    font.bold: true
                }
                Label {
                    text: variantData ? (variantData.book_no || "") + ":" + (variantData.page_num || "") : ""
                    Layout.fillWidth: true
                }
            }
        }

        // Variant text
        GroupBox {
            title: qsTr("Variant Text")
            Layout.fillWidth: true
            Layout.fillHeight: true

            ScrollView {
                anchors.fill: parent

                TextArea {
                    id: variantTextArea
                    text: variantData ? variantData.variant_text || qsTr("No text available") : ""
                    readOnly: true
                    wrapMode: Text.Wrap
                    textFormat: Text.PlainText
                    selectByMouse: true
                    font.pixelSize: 14
                }
            }
        }

        // Notes and additional information
        GroupBox {
            title: qsTr("Notes")
            Layout.fillWidth: true
            visible: variantData && variantData.notes

            ScrollView {
                height: 80
                width: parent.width

                TextArea {
                    text: variantData ? variantData.notes || "" : ""
                    readOnly: true
                    wrapMode: Text.Wrap
                    textFormat: Text.PlainText
                    font.pixelSize: 12
                    font.italic: true
                }
            }
        }

        // Buttons
        RowLayout {
            Layout.fillWidth: true

            Button {
                text: qsTr("Copy Text")
                onClicked: {
                    variantTextArea.selectAll()
                    variantTextArea.copy()
                    variantTextArea.deselect()
                    copyConfirmation.open()
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                text: qsTr("Close")
                onClicked: variantPopup.close()
            }
        }
    }

    // Helper function to get manuscript name from sigla
    function getManuscriptName(sigla) {
        if (!sigla) return qsTr("Unknown")

        var manuscriptMap = {
            "Cb": qsTr("Cambridge (Cb)"),
            "Ba": qsTr("Bangkok A (Ba)"),
            "Bb": qsTr("Bangkok B (Bb)"),
            "Bc": qsTr("Bangkok C (Bc)"),
            "L": qsTr("London (L)"),
            "P": qsTr("Paris (P)"),
            "R": qsTr("Rome (R)"),
            "S": qsTr("Sri Lanka (S)"),
            "T": qsTr("Thai (T)"),
            "U": qsTr("Uppsala (U)"),
            "V": qsTr("Vatican (V)")
        }

        return manuscriptMap[sigla] || qsTr("Manuscript %1").arg(sigla)
    }

    // Copy confirmation dialog
    MessageDialog {
        id: copyConfirmation
        title: qsTr("Copied")
        text: qsTr("Variant text copied to clipboard.")
        buttons: MessageDialog.Ok
    }

    // Keyboard shortcuts
    Shortcut {
        sequences: [StandardKey.Copy]
        onActivated: {
            variantTextArea.selectAll()
            variantTextArea.copy()
            variantTextArea.deselect()
        }
    }

    Shortcut {
        sequences: [StandardKey.Cancel, "Esc"]
        onActivated: variantPopup.close()
    }
}
