from cg_algorithms import *

import sys
from enum import Enum

from PyQt5.QtCore import Qt, QRectF

from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    qApp,
    QApplication,
    QMenu,
    QLabel,
    QColorDialog,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsItem,
    QGraphicsScene,
    QPushButton,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QLayout)


from PyQt5.QtGui import QIcon, QColor, QPainter, QPalette, QImage, QPixmap, QMouseEvent


class Acting(Enum):
    Free = 0

    Translate = 1
    Rotate = 2
    Scale = 3
    Clip = 4

    Line = 5
    Polygon = 6
    Ellipse = 7
    Curve = 8


class Element(QGraphicsItem):
    class ListItem(QListWidgetItem):
        def __init__(self, element, *args):
            super().__init__(*args)
            self.element = element

    def __init__(self, id: str, primitive: Primitive, color: Color, parent=None):
        super().__init__(parent=parent)
        self.id = id
        self.primitive: Primitive = primitive
        self.color: Color = color
        self.listItem: self.ListItem = self.ListItem(self, self.__str__())
        self.canvas: MainCanvas = None

    def __str__(self):
        return self.id + " " + self.primitive.__str__()

    def paint(self, painter: QPainter, option, widget=None):
        c = QColor()
        c.setRgb(*self.color)
        painter.setPen(c)
        for p in self.primitive.render():
            painter.drawPoint(*p)
        if self.listItem.isSelected():
            pen = painter.pen()
            c.setAlpha(96)
            painter.setPen(c)
            painter.drawRect(self.boundingRect())

    def boundingRect(self) -> QRectF:
        return QRectF(*self.primitive.boundingRect())

    # def mousePressEvent(self, event: QMouseEvent):
    #     self.canvas.selectElementFromCanvas(self)


class MainCanvas(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent=parent)
        self.main: MainWindow = parent
        self.listWidget: QListWidget = QListWidget(parent)
        self.listWidget.itemSelectionChanged.connect(self.onSelectChanged)

        self.scene: QGraphicsScene = scene
        self.scene.setBackgroundBrush(Qt.white)

        self.elements = {}
        self.selecting: Element = None

        self.pointList = []
        # self.helperCanvasItems = []

    def clearSelection(self):
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            item.setSelected(False)
        self.scene.update()

    def selectElementFromCanvas(self, e: Element):
        self.clearSelection()
        e.listItem.setSelected(True)

    def onSelectChanged(self):
        items = self.listWidget.selectedItems()
        if not items:
            self.selecting = None
            self.main.infoStatusLabel.setText("")
            return
        self.selecting = items[0]
        self.main.infoStatusLabel.setText(
            "Selecting: " + items[0].element.__str__())
        self.scene.update(self.scene.sceneRect())

    def addElement(self, e: Element):
        e.canvas = self
        self.elements[e.id] = e
        self.scene.addItem(e)
        self.listWidget.addItem(e.listItem)

    def delElement(self, id: str):
        try:
            e = self.elements[id]
            self.scene.removeItem(e)
            self.listWidget.takeItem(
                self.listWidget.indexFromItem(e.listItem).row())
            del self.elements[id]

        except Exception as e:
            print(e)

        self.clearSelection()

    def getElement(self, id: str) -> Element:
        try:
            return self.elements[id]
        except Exception as e:
            print(e)

    def clearElement(self):
        keys = [_ for _ in self.elements]
        for key in keys:
            self.delElement(key)

    def updateElement(self, id: str):
        e = self.getElement(id)
        if e:
            self.scene.update()
            e.listItem.setText(e.__str__())

    def translateElement(self, id: str, dx: int, dy: int):
        e = self.getElement(id)
        if not e:
            return
        e.primitive.translate(dx, dy)
        self.updateElement(id)

    def rotateElement(self, id: str, x0: int, y0: int, deg: int):
        e = self.getElement(id)
        if not e:
            return
        e.primitive.rotate(x0, y0, deg)
        self.updateElement(id)

    def scaleElement(self, id: str, x0: int, y0: int, rate: float):
        e = self.getElement(id)
        if not e:
            return
        e.primitive.scale(x0, y0, rate)
        self.updateElement(id)

    def clipElement(self, id: str, x0: int, y0: int, x1: int, y1: int, algorithm: Line.ClipAlgorithm):
        e = self.getElement(id)
        if not e or e.primitive.type != Primitive.PType.line:
            return
        if e.primitive.clip(x0, y0, x1, y1, algorithm):
            self.updateElement(id)
        else:
            self.delElement(id)

    # def clearHelperCanvasItems(self):
    #     for i in self.helperCanvasItems:
    #         self.scene.removeItem(i)
    #     self.helperCanvasItems = []

    def mousePressEvent(self, event: QMouseEvent):
        pos = self.mapToScene(event.localPos().toPoint())
        x, y = int(pos.x()), int(pos.y())
        if self.main.acting == Acting.Free:
            minSquare = 10000 ** 2
            targetE: Element = None
            for id in self.elements:
                e = self.elements[id]
                rect = e.boundingRect()
                if e.boundingRect().contains(x, y) and rect.width()*rect.height() < minSquare:
                    targetE = e
                    minSquare = rect.width()*rect.height()
            if targetE:
                self.selectElementFromCanvas(targetE)
            else:
                self.main.updateActingStatus(Acting.Free)
                self.clearSelection()
        else:
            self.pointList.append((x, y))
            if self.main.acting == Acting.Line:
                if len(self.pointList) >= 2:
                    self.main.addElement(
                        Line(*self.pointList[0], *self.pointList[1], Line.Algorithm.DDA))
                    self.main.bLine.toggle()
            elif self.main.acting == Acting.Polygon:
                pass
            elif self.main.acting == Acting.Ellipse:
                pass
            elif self.main.acting == Acting.Curve:
                pass
            elif self.main.acting == Acting.Translate:
                pass
            elif self.main.acting == Acting.Rotate:
                pass
            elif self.main.acting == Acting.Scale:
                pass
            elif self.main.acting == Acting.Clip and self.selecting.primitive.type == Primitive.PType.line:
                pass

        self.scene.update()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.acting: Acting = Acting.Free
        self.color = (0, 0, 0)
        self.size = (0, 0)
        self.scene = QGraphicsScene(self)
        self.canvas = MainCanvas(self.scene, self)

        self.initUI()

        self.id = 0
        self.setColor(0, 0, 0)
        self.resetSize(500, 500)
        self.updateActingStatus(Acting.Free)

        self.addElement(Line(100, 400, 300, 200, Line.Algorithm.DDA))
        self.addElement(Line(200, 200, 400, 400, Line.Algorithm.Bresenham))
        self.setColor(96, 211, 148)
        self.addElement(Ellipse(200, 100, 350, 460))
        self.setColor(255, 0, 0)
        self.addElement(
            Polygon([(0, 0), (100, 200), (300, 100)], Line.Algorithm.Bresenham))
        self.setColor(0, 255, 0)
        self.addElement(
            Curve([(0, 0), (100, 200), (300, 100)], Curve.Algorithm.B_spline))

    def initUI(self):

        self.setWindowTitle("CG2020 Drawing Board")
        self.statusBar()

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        self.setGeometry(300, 300, 1200, 800)

        self.initStatusBar()
        self.initMenu()
        self.initMain()

        self.show()

    def initStatusBar(self):
        self.infoStatusLabel = QLabel("", self)
        self.statusBar().insertPermanentWidget(0, self.infoStatusLabel)
        self.sizeStatusLabel = QLabel("", self)
        self.statusBar().insertPermanentWidget(1, self.sizeStatusLabel)
        self.colorStatusLabel = QLabel("", self)
        self.statusBar().insertPermanentWidget(2, self.colorStatusLabel)

    def updateActingStatus(self, acting: Acting):
        self.acting = acting

    def initMenu(self):
        self.initFileMenu()
        self.initCanvasMenu()
        self.initPrimitiveMenu()
        self.initTransformMenu()

    def initFileMenu(self):
        fileMenu = self.menuBar().addMenu('&File')

        # Load action
        # loadAction = QAction('&Load', self)
        # loadAction.setStatusTip('Load from script')
        # loadAction.setShortcut('Ctrl+L')
        # fileMenu.addAction(loadAction)

        # Save action
        saveAction = QAction('&Save', self)
        saveAction.setStatusTip('Save the canvas')
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.getSaveDialog)
        fileMenu.addAction(saveAction)

        # Exit action
        exitAction = QAction('&Exit', self)
        exitAction.setStatusTip('Exit application')
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)

    def saveFile(self, name: str):
        self.canvas.clearSelection()
        img = QImage(self.size[0], self.size[1], QImage.Format_ARGB32)
        painter = QPainter(img)
        self.scene.render(painter)
        img.save(name)
        painter.end()

    def getSaveDialog(self):
        fileName = QFileDialog.getSaveFileName(
            self, "Save Canvas", "output.bmp", "Images (*.bmp)")[0]
        if not fileName:
            return
        try:
            self.saveFile(fileName)
        except Exception as e:
            print(e)

    def initCanvasMenu(self):
        canvasMenu = self.menuBar().addMenu('&Canvas')

        # Reset action
        resetAction = QAction('&Reset', self)
        resetAction.setStatusTip('Reset the canvas')
        resetAction.setShortcut('Ctrl+R')
        resetAction.triggered.connect(self.getResetDialog)
        canvasMenu.addAction(resetAction)

        # Set color
        colorAction = QAction('&Color', self)
        colorAction.setStatusTip('Set pen color')
        colorAction.setShortcut('Ctrl+P')
        colorAction.triggered.connect(self.pickColor)
        canvasMenu.addAction(colorAction)

        # Delete
        deleteAction = QAction('&Delete', self)
        deleteAction.setStatusTip('Delete primitive')
        deleteAction.setShortcut('Ctrl+D')
        deleteAction.triggered.connect(self.getDeleteDialog)
        canvasMenu.addAction(deleteAction)

    def getResetDialog(self):
        text, ok = QInputDialog().getText(
            self, f"Reset Canvas", "width height(empty for keep current size)", echo=QLineEdit.Normal)
        if not ok:
            return
        args = []
        try:
            args = list(map(lambda s: int(s), text.split()))
        except Exception as e:
            print(e)
        if len(args) == 0:
            self.resetSize(*self.size)
        elif len(args) == 2:
            self.resetSize(*args)

    def resetSize(self, width: int, height: int):
        if width < 100 or width > 1000 or height < 100 or height > 1000:
            return
        self.id = 0
        self.canvas.clearElement()
        self.size = (width, height)
        self.scene.clear()
        self.scene.setSceneRect(0, 0, width, height)
        self.scene.addRect(-1, -1, width+2, height+2)
        self.canvas.setFixedSize(width*1.05, height*1.05)
        self.adjustSize()
        self.sizeStatusLabel.setText(f"Size: ({width},{height})")

    def getNewID(self) -> str:
        self.id += 1
        return str(self.id)

    def getDeleteDialog(self):
        text, ok = QInputDialog().getText(
            self, f"Reset Canvas", "width height(empty for keep current size)", echo=QLineEdit.Normal)
        if not ok or not text:
            return
        self.canvas.delElement(text)

    def initPrimitiveMenu(self):
        primitiveMenu = self.menuBar().addMenu('&Primitive')

        # Line
        lineMenu = QMenu('&Line', self)
        # DDA
        lineActionDDA = QAction('&DDA', self)
        lineActionDDA.setStatusTip('Draw line with DDA algorithm')
        lineActionDDA.triggered.connect(
            self.getLineDialog(Line.Algorithm.DDA))
        lineMenu.addAction(lineActionDDA)
        # Bresenham
        lineActionBresenham = QAction('&Bresenham', self)
        lineActionBresenham.setStatusTip('Draw line with Bresenham algorithm')
        lineMenu.addAction(lineActionBresenham)
        lineActionBresenham.triggered.connect(
            self.getLineDialog(Line.Algorithm.Bresenham))
        primitiveMenu.addMenu(lineMenu)

        # Polygon
        polygonMenu = QMenu('&Polygon', self)
        # DDA
        polygonActionDDA = QAction('&DDA', self)
        polygonActionDDA.setStatusTip('Draw polygon with DDA algorithm')
        polygonActionDDA.triggered.connect(
            self.getPolygonDialog(Line.Algorithm.DDA))
        polygonMenu.addAction(polygonActionDDA)
        # Bresenham
        polygonActionBresenham = QAction('&Bresenham', self)
        polygonActionBresenham.setStatusTip(
            'Draw polygon with Bresenham algorithm')
        polygonMenu.addAction(polygonActionBresenham)
        polygonActionBresenham.triggered.connect(
            self.getPolygonDialog(Line.Algorithm.Bresenham))
        primitiveMenu.addMenu(polygonMenu)

        # Ellipse
        ellipseAction = QAction('&Ellipse', self)
        ellipseAction.setStatusTip('Draw ellipse')
        ellipseAction.triggered.connect(self.getEllipseDialog())
        primitiveMenu.addAction(ellipseAction)

        # Curve
        # Bezier
        curveMenu = QMenu('&Curve', self)
        curveActionBezier = QAction('&Bezier', self)
        curveActionBezier.setStatusTip('Draw curve with Bezier algorithm')
        curveActionBezier.triggered.connect(
            self.getCurveDialog(Curve.Algorithm.Bezier))
        curveMenu.addAction(curveActionBezier)
        # B Spline
        curveActionB_spline = QAction('&B-spline', self)
        curveActionB_spline.setStatusTip('Draw curve with B-spline algorithm')
        curveActionB_spline.triggered.connect(
            self.getCurveDialog(Curve.Algorithm.B_spline))
        curveMenu.addAction(curveActionB_spline)

        primitiveMenu.addMenu(curveMenu)

    def getLineDialog(self, algorithm: Line.Algorithm):
        def f():
            text, ok = QInputDialog().getText(
                self, f"Draw Line({algorithm.name})", "x0 y0 x1 y1", echo=QLineEdit.Normal)
            if not ok:
                return
            args = []
            try:
                args = list(map(lambda s: int(s), text.split()))
            except Exception as e:
                print(e)
            if len(args) == 4:
                self.addElement(Line(*args, algorithm))
        return f

    def getPolygonDialog(self, algorithm: Line.Algorithm):
        def f():
            text, ok = QInputDialog().getText(
                self, f"Draw Polygon({algorithm.name})", "x0 y0 x1 y1 x2 y2 ...", echo=QLineEdit.Normal)
            if not ok:
                return
            args = []
            try:
                args = list(map(lambda s: int(s), text.split()))
            except Exception as e:
                print(e)
            points = []
            for i in range(len(args) // 2):
                points.append((args[i*2], args[i*2+1]))
            if points:
                self.addElement(Polygon(points, algorithm))
        return f

    def getEllipseDialog(self):
        def f():
            text, ok = QInputDialog().getText(
                self, "Draw Ellipse", "x0 y0 x1 y1 ...", echo=QLineEdit.Normal)
            if not ok:
                return
            args = []
            try:
                args = list(map(lambda s: int(s), text.split()))
            except Exception as e:
                print(e)
            if len(args) == 4:
                self.addElement(Ellipse(*args))
        return f

    def getCurveDialog(self, algorithm: Curve.Algorithm):
        def f():
            text, ok = QInputDialog().getText(
                self, f"Draw Curve({algorithm.name})", "x0 y0 x1 y1 x2 y2 ...", echo=QLineEdit.Normal)
            if not ok:
                return
            args = []
            try:
                args = list(map(lambda s: int(s), text.split()))
            except Exception as e:
                print(e)
            points = []
            for i in range(len(args) // 2):
                points.append((args[i*2], args[i*2+1]))
            if points:
                self.addElement(Curve(points, algorithm))
        return f

    def initTransformMenu(self):
        transformMenu = self.menuBar().addMenu('&Transform')

        # Translate
        translateAction = QAction('&Translate', self)
        translateAction.setStatusTip('Translate primitive')
        translateAction.triggered.connect(self.getTranslateDialog)
        transformMenu.addAction(translateAction)

        # Rotate
        rotateAction = QAction('&Rotate', self)
        rotateAction.setStatusTip('Rotate any primitive')
        rotateAction.triggered.connect(self.getRotateDialog)
        transformMenu.addAction(rotateAction)

        # Scale
        scaleAction = QAction('&Scale', self)
        scaleAction.setStatusTip('Scale any primitive')
        scaleAction.triggered.connect(self.getScaleDialog)
        transformMenu.addAction(scaleAction)

        # Clip
        clipMenu = QMenu('&Clip', self)
        # Cohen-Sutherland
        clipActionCohen = QAction('&Cohen-Sutherland', self)
        clipActionCohen.setStatusTip(
            'Clip line with Cohen-Sutherland algorithm')
        clipActionCohen.triggered.connect(
            self.getClipDialog(Line.ClipAlgorithm.Cohen_Sutherland))
        clipMenu.addAction(clipActionCohen)
        # Liang-Barsky
        clipActionLiang = QAction('&Liang-Barsky', self)
        clipActionLiang.setStatusTip('Clip line with Liang-Barsky algorithm')
        clipActionLiang.triggered.connect(
            self.getClipDialog(Line.ClipAlgorithm.Liang_Barsky))
        clipMenu.addAction(clipActionLiang)
        transformMenu.addMenu(clipMenu)

    def getTranslateDialog(self):
        text, ok = QInputDialog().getText(
            self, f"Translate", "id dx dy", echo=QLineEdit.Normal)
        if not ok or not text:
            return
        try:
            args = text.split()
            self.canvas.translateElement(args[0], int(args[1]), int(args[2]))
        except Exception as e:
            print(e)

    def getRotateDialog(self):
        text, ok = QInputDialog().getText(
            self, f"Rotate", "id x0 y0 degree", echo=QLineEdit.Normal)
        if not ok or not text:
            return
        try:
            args = text.split()
            self.canvas.rotateElement(
                args[0], int(args[1]), int(args[2]), int(args[3]))
        except Exception as e:
            print(e)

    def getScaleDialog(self):
        text, ok = QInputDialog().getText(
            self, f"Scale", "id x0 y0 rate", echo=QLineEdit.Normal)
        if not ok or not text:
            return
        try:
            args = text.split()
            self.canvas.scaleElement(
                args[0], int(args[1]), int(args[2]), float(args[3]))
        except Exception as e:
            print(e)

    def getClipDialog(self, algorithm: Line.ClipAlgorithm):
        def f():
            text, ok = QInputDialog().getText(
                self, f"Clip", "id x0 y0 x1 x2", echo=QLineEdit.Normal)
            if not ok or not text:
                return
            try:
                args = text.split()
                self.canvas.clipElement(
                    args[0], int(args[1]), int(args[2]),
                    int(args[3]), int(args[4]), algorithm)
            except Exception as e:
                print(e)
        return f

    def initMain(self):
        mainWidget = QWidget(self)
        self.setCentralWidget(mainWidget)
        horizonLayout = QHBoxLayout(mainWidget)

        # Toolbar
        self.initToolBar()
        horizonLayout.addLayout(self.toolBar)

        # Canvas
        horizonLayout.addWidget(self.canvas, alignment=Qt.AlignTop)

        # Spacing
        horizonLayout.addSpacerItem(QSpacerItem(
            0, 0, hPolicy=QSizePolicy.Expanding, vPolicy=QSizePolicy.Expanding))

        # List
        self.canvas.listWidget.setFixedWidth(200)
        horizonLayout.addWidget(self.canvas.listWidget)

    def initToolBar(self):
        self.toolBar = QGridLayout()
        self.toolBar.setVerticalSpacing(5)
        self.toolBar.setHorizontalSpacing(5)
        col = 0
        widthFull = 3

        # Canvas
        self.toolBar.addWidget(QLabel("Canvas"), col, 0, 1, widthFull)
        col += 1

        # Clear
        def bClearFunc():
            mBox = QMessageBox()
            mBox.setText("The canvas will be cleared.")
            mBox.setInformativeText("Are you sure?")
            mBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            mBox.setDefaultButton(QMessageBox.No)
            if mBox.exec_() == QMessageBox.Yes:
                self.resetSize(*self.size)
        bClear = QPushButton("Clear")
        bClear.clicked.connect(bClearFunc)
        self.toolBar.addWidget(bClear, col, 0, 1, widthFull)
        col += 1

        # Delete
        def bDeleteFunc():
            if self.canvas.selecting:
                self.canvas.delElement(self.canvas.selecting.element.id)
        bDelete = QPushButton("Delete")
        bDelete.clicked.connect(bDeleteFunc)
        self.toolBar.addWidget(bDelete, col, 0, 1, widthFull)
        col += 1

        # Primitives
        self.toolBar.addWidget(QLabel("Primitive"), col, 0, 1, widthFull)
        col += 1

        def bLineFunc(isDown: bool):
            if isDown:
                self.canvas.clearSelection()
                self.updateActingStatus(Acting.Line)
                self.canvas.pointList = []
                return
            self.canvas.pointList = []
            self.updateActingStatus(Acting.Free)
        bLine = QPushButton("Line")
        self.bLine = bLine
        bLine.setCheckable(True)
        bLine.toggled.connect(bLineFunc)
        self.toolBar.addWidget(bLine, col, 0, 1, widthFull)
        col += 1
        self.toolBar.addWidget(QPushButton("Polygon"), col, 0, 1, widthFull)
        col += 1
        self.toolBar.addWidget(QPushButton("Ellipse"), col, 0, 1, widthFull)
        col += 1
        self.toolBar.addWidget(QPushButton("Curve"), col, 0, 1, widthFull)
        col += 1

        # Transform
        self.toolBar.addWidget(QLabel("Transform"), col, 0, 1, widthFull)
        col += 1
        self.toolBar.addWidget(QPushButton("Translate"), col, 0, 1, widthFull)
        col += 1
        self.toolBar.addWidget(QPushButton("Rotate"), col, 0, 1, widthFull)
        col += 1
        self.toolBar.addWidget(QPushButton("Scale"), col, 0, 1, widthFull)
        col += 1
        self.toolBar.addWidget(QPushButton("Clip"), col, 0, 1, widthFull)
        col += 1

        # Color
        self.toolBar.addWidget(QLabel("Color"), col, 0, 1, widthFull)
        col += 1
        colors = [
            [(0, 0, 0), (85, 85, 85), (170, 170, 170)],
            [(255, 0, 0), (0, 255, 0), (0, 0, 255)],
            [(0, 255, 255), (255, 0, 255), (255, 255, 0)],
            [(223, 96, 85), (96, 211, 148), (170, 246, 231)],
            [(203, 144, 77), (223, 203, 116), (195, 233, 145)],
            [(180, 206, 179), (219, 211, 201), (250, 212, 216)],
        ]

        def getSetColor(main, r: int, g: int, b: int):
            def f():
                return main.setColor(r, g, b)
            return f

        for cs in colors:
            for i in range(len(cs)):

                b1 = QPushButton(u"\u25A0")
                b1.setStyleSheet(
                    f"QPushButton {{color:rgb({cs[i][0]},{cs[i][1]},{cs[i][2]});}}")
                b1.clicked.connect(getSetColor(self, *cs[i]))
                self.toolBar.addWidget(b1, col, i, 1, 1)

            col += 1

        # Spacer
        self.toolBar.addItem(QSpacerItem(
            0, 0, hPolicy=QSizePolicy.Expanding, vPolicy=QSizePolicy.Expanding), col, 0, 1, widthFull)

    def setColor(self, r: int, g: int, b: int):
        self.color = (r, g, b)
        self.colorStatusLabel.setText(f"Color: ({r},{g},{b})")

    def pickColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            c = color.getRgb()
            self.setColor(c[0], c[1], c[2])

    def addElement(self, primitive: Primitive):
        self.canvas.addElement(Element(self.getNewID(), primitive, self.color))

    def delElement(self, id: str):
        self.canvas.delElement(id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec_())
