// MainWindow.qml
// Main application window for Tipitaka PTS Browser

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Dialogs

ApplicationWindow {
    id: mainWindow
    title: qsTr("Tipitaka PTS Browser")
    width: 1200
    height: 800
    visible: true
    color: palette.window

    // Property to access the Python backend
    property var tipitakaBrowser

    // Application state
    property string currentTextId: ""
    property string currentTextContent: ""
    property string currentEdition: "PTS"
    property var searchResults: []
    property var bookmarks: []
    property var settings: ({
        showLineNumbers: true,
        wordWrap: true,
        fontSize: 14,
        default_edition: "PTS"
    })
    property bool isLoading: false
    property var navigationStack: []
    property int wordCount: 0
    property var apparatusVariants: []
    property var dictionaryEntry: null
    property bool showThaiScript: false
    property string thaiTextContent: ""
    property string currentThaiTextId: ""
    property var textTreeModel: []
    property var activeTextView: ptsTextView

    Component.onCompleted: {
        loadSettings()
        loadBookmarks()
        loadTextTree()
        loadText("M I 3")
    }

    // Color palette
    SystemPalette {
        id: palette
        colorGroup: SystemPalette.Active
    }

    // Font settings (resources not available, using system fonts)
    /*
    FontLoader {
        id: paliFont
        source: "qrc:/fonts/NotoSansPali-Regular.ttf"
    }

    FontLoader {
        id: myanmarFont
        source: "qrc:/fonts/NotoSansMyanmar-Regular.ttf"
    }

    FontLoader {
        id: devanagariFont
        source: "qrc:/fonts/NotoSansDevanagari-Regular.ttf"
    }
    */

    // Menu bar
    menuBar: MenuBar {
        Menu {
            title: qsTr("&File")

            Action {
                text: qsTr("&Open Text...")
                shortcut: StandardKey.Open
                onTriggered: fileDialog.open()
            }

            MenuSeparator {}

            Action {
                text: qsTr("&Export as PDF...")
                onTriggered: exportDialog.open()
            }

            Action {
                text: qsTr("Export as &HTML...")
                onTriggered: exportHtmlDialog.open()
            }

            MenuSeparator {}

            Action {
                text: qsTr("&Settings")
                shortcut: StandardKey.Preferences
                onTriggered: settingsWindow.open()
            }

            MenuSeparator {}

            Action {
                text: qsTr("E&xit")
                shortcut: StandardKey.Quit
                onTriggered: Qt.quit()
            }
        }

        Menu {
            title: qsTr("&Edit")

            Action {
                text: qsTr("&Find")
                shortcut: StandardKey.Find
                onTriggered: searchField.forceActiveFocus()
            }

            Action {
                text: qsTr("Find &Next")
                shortcut: StandardKey.FindNext
                onTriggered: activeTextView ? activeTextView.findNext() : null
            }

            Action {
                text: qsTr("Find &Previous")
                shortcut: StandardKey.FindPrevious
                onTriggered: activeTextView ? activeTextView.findPrevious() : null
            }

            MenuSeparator {}

            Action {
                text: qsTr("&Copy")
                shortcut: StandardKey.Copy
                enabled: activeTextView ? activeTextView.selectedText !== "" : false
                onTriggered: activeTextView ? activeTextView.copy() : null
            }

            Action {
                text: qsTr("Select &All")
                shortcut: StandardKey.SelectAll
                onTriggered: activeTextView ? activeTextView.selectAll() : null
            }
        }

        Menu {
            title: qsTr("&View")

            Menu {
                title: qsTr("&Edition")

                Action {
                    text: "PTS"
                    checkable: true
                    checked: currentEdition === "PTS"
                    onTriggered: {
                        currentEdition = "PTS"
                        loadText(currentTextId)
                    }
                }

                Action {
                    text: "ROTA"
                    checkable: true
                    checked: currentEdition === "ROTA"
                    onTriggered: {
                        currentEdition = "ROTA"
                        loadText(currentTextId)
                    }
                }
            }

            MenuSeparator {}

            Action {
                text: qsTr("&Increase Font Size")
                shortcut: StandardKey.ZoomIn
                onTriggered: settings.fontSize = Math.min(settings.fontSize + 1, 36)
            }

            Action {
                text: qsTr("&Decrease Font Size")
                shortcut: StandardKey.ZoomOut
                onTriggered: settings.fontSize = Math.max(settings.fontSize - 1, 8)
            }

            Action {
                text: qsTr("&Reset Font Size")
                shortcut: "Ctrl+0"
                onTriggered: settings.fontSize = 12
            }

            MenuSeparator {}

            Action {
                text: qsTr("&Show Line Numbers")
                checkable: true
                checked: settings.showLineNumbers !== undefined ? settings.showLineNumbers : true
                onTriggered: settings.showLineNumbers = !settings.showLineNumbers
            }

            Action {
                text: qsTr("&Word Wrap")
                checkable: true
                checked: settings.wordWrap !== undefined ? settings.wordWrap : true
                onTriggered: settings.wordWrap = !settings.wordWrap
            }

            MenuSeparator {}

            Action {
                text: qsTr("Show &Thai Script")
                checkable: true
                checked: showThaiScript
                onTriggered: {
                    showThaiScript = !showThaiScript
                    // Save setting
                    if (tipitakaBrowser) {
                        var currentSettings = tipitakaBrowser.loadSettings()
                        currentSettings.show_thai_script = showThaiScript
                        tipitakaBrowser.saveSettings(currentSettings)
                    }
                    // Reload current text to update Thai script view
                    if (currentTextId) {
                        loadText(currentTextId)
                    }
                }
            }

            }

            Action {
                text: qsTr("&Word Wrap")
                checkable: true
                checked: settings.wordWrap !== undefined ? settings.wordWrap : true
                onTriggered: settings.wordWrap = !settings.wordWrap
            }
        }

        Menu {
            title: qsTr("&Bookmarks")

            Action {
                text: qsTr("&Add Bookmark")
                shortcut: "Ctrl+B"
                onTriggered: addBookmarkDialog.open()
            }

            Action {
                text: qsTr("&Manage Bookmarks")
                onTriggered: bookmarksWindow.open()
            }

            MenuSeparator {}

            Repeater {
                model: bookmarks.slice(0, 10) // Show only first 10 bookmarks in menu

                Action {
                    text: modelData.text_id + " - " + (modelData.note || qsTr("Bookmark"))
                    onTriggered: {
                        currentTextId = modelData.text_id
                        loadText(modelData.text_id)
                        textView.cursorPosition = modelData.position
                    }
                }
            }
        }

        Menu {
            title: qsTr("&Help")

            Action {
                text: qsTr("&User Guide")
                onTriggered: helpWindow.open()
            }

            Action {
                text: qsTr("&Keyboard Shortcuts")
                onTriggered: shortcutsWindow.open()
            }

            MenuSeparator {}

            Action {
                text: qsTr("&About")
                onTriggered: aboutDialog.open()
            }
        }

    // Toolbar
    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            spacing: 5

            ToolButton {
                text: qsTr("◀")
                ToolTip.text: qsTr("Previous Text")
                enabled: navigationStack.length > 1
                onClicked: {
                    if (navigationStack.length > 1) {
                        navigationStack.pop()
                        var prev = navigationStack[navigationStack.length - 1]
                        currentTextId = prev.textId
                        currentEdition = prev.edition
                        loadText(currentTextId)
                    }
                }
            }

            ToolButton {
                text: qsTr("▶")
                ToolTip.text: qsTr("Next Text")
                enabled: false
            }

            ToolSeparator {}

            ComboBox {
                id: editionCombo
                Layout.preferredWidth: 150
                model: tipitakaBrowser ? tipitakaBrowser.getAvailableEditions(currentTextId) : ["PTS"]
                currentIndex: model.indexOf(currentEdition)
                onActivated: {
                    currentEdition = model[currentIndex]
                    loadText(currentTextId)
                }
            }

            ToolSeparator {}

            TextField {
                id: searchField
                Layout.fillWidth: true
                placeholderText: qsTr("Search in texts...")
                onAccepted: performSearch(text)
            }

            ToolButton {
                text: qsTr("🔍")
                ToolTip.text: qsTr("Search")
                onClicked: performSearch(searchField.text)
            }

            ToolSeparator {}

            ToolButton {
                text: qsTr("📖")
                ToolTip.text: qsTr("Dictionary Lookup")
                onClicked: dictionaryWindow.open()
            }

            ToolButton {
                text: qsTr("⭐")
                ToolTip.text: qsTr("Add Bookmark")
                onClicked: addBookmarkDialog.open()
            }

            ToolButton {
                text: qsTr("📊")
                ToolTip.text: qsTr("Statistics")
                onClicked: statisticsWindow.open()
            }
        }
    }

    // Status bar
    footer: Rectangle {
        height: 28
        color: palette.alternateBase
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8
            anchors.rightMargin: 8

            Label {
                id: statusLabel
                text: isLoading ? qsTr("Loading...") :
                       currentTextId ? qsTr("Loaded: %1").arg(currentTextId) :
                       qsTr("Ready")
            }

            Item { Layout.fillWidth: true }

            Label {
                text: qsTr("Edition: %1").arg(currentEdition)
            }

            Label {
                text: qsTr("Words: %1").arg(wordCount)
            }
        }
    } // end footer Rectangle

    // Main content area
    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        // Left panel - Navigation and search results
        ScrollView {
            id: leftPanel
            SplitView.preferredWidth: 300
            SplitView.minimumWidth: 200
            SplitView.maximumWidth: 500

            ColumnLayout {
                width: leftPanel.width
                spacing: 10

                GroupBox {
                    title: qsTr("Text Navigation")
                    Layout.fillWidth: true

                    ListView {
                        id: textTree
                        Layout.fillWidth: true
                        Layout.preferredHeight: 300
                        model: textTreeModel
                        clip: true

                        delegate: ItemDelegate {
                            width: textTree.width
                            text: modelData.display || qsTr("Item")
                            enabled: modelData.text_id !== undefined && modelData.text_id !== ""
                            font.bold: !enabled
                            leftPadding: enabled ? 16 : 8
                            opacity: enabled ? 1.0 : 0.7
                            onClicked: {
                                if (modelData.text_id) {
                                    loadTextFromTree(modelData.text_id)
                                }
                            }
                        }

                        Label {
                            anchors.centerIn: parent
                            text: qsTr("Loading navigation tree...")
                            visible: textTreeModel.length === 0
                            color: palette.mid
                        }
                    }
                }

                GroupBox {
                    title: qsTr("Search Results")
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ListView {
                        id: searchResultsList
                        width: parent.width
                        height: 200
                        model: searchResults
                        clip: true

                        delegate: ItemDelegate {
                            width: searchResultsList.width
                            text: modelData.title || modelData.text_id
                            onClicked: {
                                currentTextId = modelData.text_id
                                currentEdition = modelData.edition || "PTS"
                                loadText(currentTextId)
                            }
                        }

                        Label {
                            anchors.centerIn: parent
                            text: qsTr("No search results")
                            visible: searchResults.length === 0
                            color: palette.mid
                        }

                        // Update activeTextView when tab changes
                        onCurrentIndexChanged: {
                            if (currentIndex === 0) {
                                activeTextView = ptsTextView
                            } else if (currentIndex === 1) {
                                activeTextView = thaiTextView
                            }
                        }
                    }
                }
            }
        }

        // Main text area with tabs for PTS/Thai view
        ColumnLayout {
            id: textColumn
            SplitView.fillWidth: true
            SplitView.fillHeight: true
            spacing: 0

            // Tab bar for PTS/Thai view
            TabBar {
                id: textTabBar
                Layout.fillWidth: true
                visible: showThaiScript && thaiTextContent !== ""

                TabButton {
                    text: qsTr("PTS Edition")
                }
                TabButton {
                    text: qsTr("Thai Script")
                }
            }

            // Stack layout for tab content
            StackLayout {
                id: textStackLayout
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: textTabBar.currentIndex

                // Tab 1: ROTA/PTS Edition
                ScrollView {
                    id: ptsScrollView
                    width: parent.width
                    height: parent.height

                    TextArea {
                        id: ptsTextView
                        width: ptsScrollView.width
                        wrapMode: (settings.wordWrap !== undefined ? settings.wordWrap : true) ? Text.Wrap : Text.NoWrap
                        readOnly: true
                        textFormat: Text.RichText
                        font.family: getFontFamily()
                        font.pixelSize: settings.fontSize !== undefined ? settings.fontSize : 14
                        selectByMouse: true
                        text: currentTextContent

                        background: Rectangle {
                            color: palette.base
                            border.color: palette.mid
                            border.width: 1
                        }

                        // Line numbers
                        leftPadding: (settings.showLineNumbers !== undefined ? settings.showLineNumbers : true) ? 40 : 10
                        topPadding: 10
                        bottomPadding: 10
                        rightPadding: 10

                        Rectangle {
                            visible: settings.showLineNumbers !== undefined ? settings.showLineNumbers : true
                            width: 30
                            height: parent.height
                            color: palette.alternateBase
                            border.color: palette.mid

                            ListView {
                                anchors.fill: parent
                                model: Math.ceil(ptsTextView.height / ptsTextView.font.pixelSize)
                                delegate: Text {
                                    width: parent.width
                                    height: ptsTextView.font.pixelSize
                                    text: index + 1
                                    color: palette.mid
                                    font: ptsTextView.font
                                    horizontalAlignment: Text.AlignRight
                                    verticalAlignment: Text.AlignVCenter
                                    rightPadding: 5
                                }
                            }
                        }
                    }
                }

                // Tab 2: Thai Script Edition
                ScrollView {
                    id: thaiScrollView
                    width: parent.width
                    height: parent.height
                    visible: showThaiScript && thaiTextContent !== ""

                    TextArea {
                        id: thaiTextView
                        width: thaiScrollView.width
                        wrapMode: (settings.wordWrap !== undefined ? settings.wordWrap : true) ? Text.Wrap : Text.NoWrap
                        readOnly: true
                        textFormat: Text.RichText
                        font.family: "Noto Sans Thai"
                        font.pixelSize: settings.fontSize !== undefined ? settings.fontSize : 14
                        selectByMouse: true
                        text: thaiTextContent !== "" ? thaiTextContent : qsTr("Thai script not available for this text")

                        background: Rectangle {
                            color: palette.base
                            border.color: palette.mid
                            border.width: 1
                        }

                        // Line numbers
                        leftPadding: (settings.showLineNumbers !== undefined ? settings.showLineNumbers : true) ? 40 : 10
                        topPadding: 10
                        bottomPadding: 10
                        rightPadding: 10

                        Rectangle {
                            visible: settings.showLineNumbers !== undefined ? settings.showLineNumbers : true
                            width: 30
                            height: parent.height
                            color: palette.alternateBase
                            border.color: palette.mid

                            ListView {
                                anchors.fill: parent
                                model: Math.ceil(thaiTextView.height / thaiTextView.font.pixelSize)
                                delegate: Text {
                                    width: parent.width
                                    height: thaiTextView.font.pixelSize
                                    text: index + 1
                                    color: palette.mid
                                    font: thaiTextView.font
                                    horizontalAlignment: Text.AlignRight
                                    verticalAlignment: Text.AlignVCenter
                                    rightPadding: 5
                                }
                            }
                        }
                    }
                }


                // Context menu
                Menu {
                    id: textContextMenu

                    Action {
                        text: qsTr("&Copy")
                        onTriggered: activeTextView ? activeTextView.copy() : null
                    }

                    Action {
                        text: qsTr("&Look Up in Dictionary")
                        onTriggered: {
                            var selected = activeTextView ? activeTextView.selectedText : ""
                            if (selected) {
                                dictionaryWindow.lookupWord(selected)
                                dictionaryWindow.open()
                            }
                        }
                    }

                    Action {
                        text: qsTr("&Add Bookmark Here")
                        onTriggered: {
                            addBookmarkDialog.position = textView.cursorPosition
                            addBookmarkDialog.open()
                        }
                    }

                    MenuSeparator {}

                    Action {
                        text: qsTr("&Search for This Text")
                        onTriggered: {
                            var selected = activeTextView ? activeTextView.selectedText : ""
                            searchField.text = selected
                            performSearch(selected)
                        }
                    }
                }


            }
        }
    }

    // Dialogs and windows
    SettingsWindow {
        id: settingsWindow
        visible: false
        tipitakaBrowser: mainWindow.tipitakaBrowser
    }

    VariantPopup {
        id: variantPopup
        visible: false
    }

    // File dialog
    FileDialog {
        id: fileDialog
        title: qsTr("Open Text File")
        nameFilters: ["Text files (*.txt)", "JSON files (*.json)", "All files (*)"]
        onAccepted: {
            // Handle file opening
            console.log("Selected file:", file)
        }
    }

    // Export dialog
    FileDialog {
        id: exportDialog
        title: qsTr("Export as PDF")
        nameFilters: ["PDF files (*.pdf)"]
        fileMode: FileDialog.SaveFile
        onAccepted: {
            // Handle PDF export
            console.log("Export to PDF:", file)
        }
    }

    FileDialog {
        id: exportHtmlDialog
        title: qsTr("Export as HTML")
        nameFilters: ["HTML files (*.html)"]
        fileMode: FileDialog.SaveFile
        onAccepted: {
            // Handle HTML export
            console.log("Export to HTML:", file)
        }
    }

    // Add bookmark dialog
    Dialog {
        id: addBookmarkDialog
        title: qsTr("Add Bookmark")
        standardButtons: Dialog.Ok | Dialog.Cancel

        property int position: 0

        ColumnLayout {
            width: 300
            spacing: 10

            Label {
                text: qsTr("Text: %1").arg(currentTextId)
            }

            Label {
                text: qsTr("Position: %1").arg(addBookmarkDialog.position)
            }

            TextField {
                id: bookmarkNoteField
                Layout.fillWidth: true
                placeholderText: qsTr("Note (optional)")
            }
        }

        onAccepted: {
            if (tipitakaBrowser) {
                tipitakaBrowser.addBookmark(currentTextId, position, bookmarkNoteField.text)
                loadBookmarks()
            }
        }
    }

    // Dictionary window
    Window {
        id: dictionaryWindow
        title: qsTr("Dictionary")
        width: 600
        height: 400
        modality: Qt.ApplicationModal

        function lookupWord(word) {
            if (tipitakaBrowser) {
                var result = tipitakaBrowser.lookupDictionary(word)
                dictionaryContent.text = formatDictionaryEntry(result)
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10

            TextField {
                id: dictionarySearchField
                Layout.fillWidth: true
                placeholderText: qsTr("Enter word to look up")
                onAccepted: dictionaryWindow.lookupWord(text)
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true

                TextArea {
                    id: dictionaryContent
                    readOnly: true
                    textFormat: Text.RichText
                    wrapMode: Text.Wrap
                    text: qsTr("Enter a word to look up in the dictionary.")
                }
            }
        }
    }

    Window {
        id: bookmarksWindow
        title: qsTr("Bookmarks")
        width: 520
        height: 360
        modality: Qt.ApplicationModal

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10

            Label {
                text: qsTr("Bookmarks (stub)")
                font.bold: true
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: bookmarks
                clip: true

                delegate: ItemDelegate {
                    width: ListView.view.width
                    text: (modelData.text_id || "") + " - " + (modelData.note || qsTr("Bookmark"))
                    onClicked: {
                        bookmarksWindow.close()
                        loadText(modelData.text_id)
                    }
                }
            }
        }
    }

    Window {
        id: statisticsWindow
        title: qsTr("Statistics")
        width: 420
        height: 220
        modality: Qt.ApplicationModal

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10

            Label { text: qsTr("Statistics (stub)") ; font.bold: true }
            Label { text: qsTr("Current text: %1").arg(currentTextId || qsTr("None")) }
            Label { text: qsTr("Words: %1").arg(wordCount) }
            Label { text: qsTr("Search results: %1").arg(searchResults.length) }
            Label { text: qsTr("Bookmarks: %1").arg(bookmarks.length) }
        }
    }

    Dialog {
        id: helpWindow
        title: qsTr("User Guide")
        standardButtons: Dialog.Ok

        Label {
            width: 420
            wrapMode: Text.Wrap
            text: qsTr("Esta es una extraccion de la GUI del AppImage. El contenido y las acciones usan stubs y no estan conectados al backend real.")
        }
    }

    Dialog {
        id: shortcutsWindow
        title: qsTr("Keyboard Shortcuts")
        standardButtons: Dialog.Ok

        Text {
            width: 380
            textFormat: Text.RichText
            text: "<b>Ctrl+O</b> Open text<br><b>Ctrl+F</b> Find<br><b>Ctrl+B</b> Add bookmark<br><b>Ctrl+Q</b> Exit"
        }
    }

    Dialog {
        id: aboutDialog
        title: qsTr("About")
        standardButtons: Dialog.Ok

        ColumnLayout {
            width: 360

            Label { text: qsTr("Tipitaka PTS Browser") ; font.bold: true }
            Label { text: qsTr("GUI extraida del AppImage") }
            Label { text: qsTr("Backend actual: stub PyQt6") }
        }
    }

    // Helper functions
    function getFontFamily() {
        switch(currentEdition) {
            case "MYANMAR": return "Noto Sans Myanmar"
            case "VRI": return "Noto Sans Devanagari"
            default: return "Sans"
        }
    }

    function loadTextTree() {
        if (!tipitakaBrowser) {
            textTreeModel = []
            return
        }
        try {
            var tree = tipitakaBrowser.getNavigationTree()
            if (tree && tree.length > 0) {
                textTreeModel = tree
                return
            }
        } catch(e) {
            console.log("getNavigationTree failed:", e)
        }
        // Fallback: minimal static tree
        textTreeModel = [
            { display: "Vinaya Piṭaka (Vin I)", text_id: "Vin I 1" },
            { display: "Dīgha Nikāya I", text_id: "D I 1" },
            { display: "Majjhima Nikāya I", text_id: "M I 1" },
            { display: "Saṃyutta Nikāya I", text_id: "S I 1" },
            { display: "Aṅguttara Nikāya I", text_id: "A I 1" },
            { display: "Suttanipāta", text_id: "Sn 1" }
        ]
    }

    function loadTextFromTree(treeItemId) {
        // This function handles loading text from tree navigation
        // treeItemId could be a PTS citation or a database ID
        loadText(treeItemId)
    }

    function loadText(textId) {
        if (!tipitakaBrowser || !textId) return

        isLoading = true
        currentTextId = textId

        // Add to navigation stack
        navigationStack.push({
            textId: textId,
            edition: currentEdition,
            timestamp: new Date()
        })

        // Load text from backend with Thai script if enabled
        var textResult = tipitakaBrowser.getText(textId, currentEdition, showThaiScript)
        if (textResult && textResult.text) {
            currentTextContent = formatText(textResult.text)

            // Load Thai script if available
            if (showThaiScript && textResult.thai_text) {
                thaiTextContent = formatText(textResult.thai_text)
                currentThaiTextId = textId
            } else {
                thaiTextContent = ""
                currentThaiTextId = ""
            }
        } else {
            currentTextContent = qsTr("Text not found: %1").arg(textId)
            thaiTextContent = ""
            currentThaiTextId = ""
        }

        isLoading = false

        // Update tab bar visibility
        textTabBar.visible = showThaiScript && thaiTextContent !== ""
    }

    function performSearch(query) {
        if (!tipitakaBrowser || !query.trim()) return

        isLoading = true
        var results = tipitakaBrowser.searchTexts(query)
        searchResults = results
        isLoading = false

        if (results.length > 0) {
            statusLabel.text = qsTr("Found %1 results").arg(results.length)
        } else {
            statusLabel.text = qsTr("No results found")
        }
    }

    function loadBookmarks() {
        if (tipitakaBrowser) {
            bookmarks = tipitakaBrowser.bookmarks || []
        }
    }

    function loadSettings() {
        if (tipitakaBrowser) {
            settings = tipitakaBrowser.loadSettings()

            // Merge loaded settings with defaults
            settings = Object.assign({
                showLineNumbers: true,
                wordWrap: true,
                fontSize: 14,
                default_edition: "PTS"
            }, settings)

            // Load Thai script setting
            if (settings.show_thai_script !== undefined) {
                showThaiScript = settings.show_thai_script
            }
            currentEdition = settings.default_edition || "ROTA"
        }
    }

    function formatText(text) {
        // Basic text formatting
        return text.replace(/\n/g, "<br>")
                   .replace(/\t/g, "&nbsp;&nbsp;&nbsp;&nbsp;")
    }

    function formatDictionaryEntry(entry) {
        if (!entry) return qsTr("No entry found")

        var html = "<h3>" + entry.word + "</h3>"
        html += "<p><b>" + qsTr("Definition") + ":</b> " + entry.definition + "</p>"

        if (entry.etymology) {
            html += "<p><b>" + qsTr("Etymology") + ":</b> " + entry.etymology + "</p>"
        }

        if (entry.examples && entry.examples.length > 0) {
            html += "<p><b>" + qsTr("Examples") + ":</b></p><ul>"
            for (var i = 0; i < entry.examples.length; i++) {
                html += "<li>" + entry.examples[i] + "</li>"
            }
            html += "</ul>"
        }

        return html
    }
}
