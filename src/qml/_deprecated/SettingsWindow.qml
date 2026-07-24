// SettingsWindow.qml
// Simple settings window for Tipitaka PTS Browser

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: settingsWindow
    title: qsTr("Settings")
    width: 500
    height: 600
    modality: Qt.ApplicationModal
    visible: false

    property var tipitakaBrowser

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        Label {
            text: qsTr("Settings")
            font.bold: true
            font.pixelSize: 16
            Layout.alignment: Qt.AlignHCenter
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                width: parent.width
                spacing: 15

                GroupBox {
                    title: qsTr("General")
                    Layout.fillWidth: true

                    GridLayout {
                        columns: 2
                        width: parent.width

                        Label { text: qsTr("Default Edition:") }
                        ComboBox {
                            id: editionCombo
                            Layout.fillWidth: true
                            model: ["ROTA", "PTS"]

                            function indexOfValue(val) {
                                for (var i = 0; i < model.length; i++) {
                                    if (model[i] === val) return i
                                }
                                return 0
                            }
                        }

                        Label { text: qsTr("Font Size:") }
                        SpinBox {
                            id: fontSizeSpin
                            Layout.fillWidth: true
                            from: 8
                            to: 36
                            value: 12
                        }
                    }
                }

                GroupBox {
                    title: qsTr("Search")
                    Layout.fillWidth: true

                    ColumnLayout {
                        width: parent.width
                        spacing: 10

                        GridLayout {
                            columns: 2
                            width: parent.width

                            Label { text: qsTr("Search Mode:") }
                            ComboBox {
                                id: searchModeCombo
                                Layout.fillWidth: true
                                model: ["Text", "Word", "Fuzzy", "Exact"]

                                function indexOfValue(val) {
                                    for (var i = 0; i < model.length; i++) {
                                        if (model[i].toLowerCase() === val.toLowerCase()) return i
                                    }
                                    return 0
                                }
                            }

                            Label { text: qsTr("Max Results:") }
                            SpinBox {
                                id: maxResultsSpin
                                Layout.fillWidth: true
                                from: 10
                                to: 200
                                value: 50
                            }
                        }
                    }
                }

                GroupBox {
                    title: qsTr("Display")
                    Layout.fillWidth: true

                    ColumnLayout {
                        width: parent.width
                        spacing: 5

                        CheckBox {
                            id: showLineNumbersCheck
                            text: qsTr("Show line numbers")
                            checked: true
                        }

                        CheckBox {
                            id: showApparatusCheck
                            text: qsTr("Show apparatus criticus")
                            checked: true
                        }

                        CheckBox {
                            id: wordWrapCheck
                            text: qsTr("Word wrap")
                            checked: true
                        }

                        CheckBox {
                            id: showThaiScriptCheck
                            text: qsTr("Show Thai script")
                            checked: false
                        }
                    }
                }

                GroupBox {
                    title: qsTr("Dictionary")
                    Layout.fillWidth: true

                    ColumnLayout {
                        width: parent.width
                        spacing: 5

                        CheckBox {
                            id: ptsDictCheck
                            text: qsTr("PTS Dictionary")
                            checked: true
                        }

                        CheckBox {
                            id: cpdDictCheck
                            text: qsTr("Critical Pali Dictionary")
                            checked: true
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true

            Button {
                text: qsTr("Cancel")
                onClicked: settingsWindow.close()
            }

            Item { Layout.fillWidth: true }

            Button {
                text: qsTr("Save")
                highlighted: true
                onClicked: {
                    if (saveSettings()) {
                        settingsWindow.close()
                    }
                }
            }
        }
    }

    function loadSettings() {
        // Load settings from browser
        if (tipitakaBrowser) {
            var settings = tipitakaBrowser.loadSettings()

            // Apply settings to UI
            editionCombo.currentIndex = editionCombo.indexOfValue(settings.default_edition || "ROTA")
            fontSizeSpin.value = settings.font_size || 12
            searchModeCombo.currentIndex = searchModeCombo.indexOfValue(settings.search_mode || "text")
            maxResultsSpin.value = settings.max_search_results || 50
            showLineNumbersCheck.checked = settings.show_line_numbers !== false
            showApparatusCheck.checked = settings.show_apparatus !== false
            wordWrapCheck.checked = settings.word_wrap !== false
            showThaiScriptCheck.checked = settings.show_thai_script || false
            ptsDictCheck.checked = (settings.dictionary_sources || ["PTS", "CPD"]).includes("PTS")
            cpdDictCheck.checked = (settings.dictionary_sources || ["PTS", "CPD"]).includes("CPD")
        }
    }

    function saveSettings() {
        if (!tipitakaBrowser) return false

        var settings = {
            default_edition: editionCombo.currentText,
            font_size: fontSizeSpin.value,
            search_mode: searchModeCombo.currentText.toLowerCase(),
            max_search_results: maxResultsSpin.value,
            show_line_numbers: showLineNumbersCheck.checked,
            show_apparatus: showApparatusCheck.checked,
            word_wrap: wordWrapCheck.checked,
            show_thai_script: showThaiScriptCheck.checked,
            dictionary_sources: getDictionarySources()
        }

        return tipitakaBrowser.saveSettings(settings)
    }

    function getDictionarySources() {
        var sources = []
        if (ptsDictCheck.checked) sources.push("PTS")
        if (cpdDictCheck.checked) sources.push("CPD")
        return sources.length > 0 ? sources : ["PTS", "CPD"]
    }

    onVisibleChanged: {
        if (visible) {
            loadSettings()
        }
    }
}
