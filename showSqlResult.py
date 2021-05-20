from itertools import product

import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from openpyxl import Workbook

import connect_mysql

dbc = connect_mysql.myDBC()



class SqlResultWin(QWidget):
    def __init__(self, sql):
        super(SqlResultWin, self).__init__()
        # self.closebut_clicked = pyqtSignal()
        self.initUI(sql)

    def initUI(self, sql):
        self.resize(1100, 800)
        self.clipboard = QApplication.clipboard()
        self.text = str()

        try:
            results, list_cols = dbc.select(sql)
            cnt_cols = len(list_cols)

            self.tableWidget = QTableWidget()
            self.tableWidget.setRowCount(len(results))  # 一定要设置行数，否则不会显示出tableWidget
            self.tableWidget.setColumnCount(cnt_cols)
            self.tableWidget.setHorizontalHeaderLabels(list_cols)  # 先设置列数后，设置表头才能生效
            self.tableWidget.horizontalHeader().setStyleSheet("color: #00007f")
            self.tableWidget.setAlternatingRowColors(True)  # 设置行背景颜色交替
            self.tableWidget.setSortingEnabled(True)
            self.tableWidget.setStyleSheet("border: 0px; alternate-background-color: #C9E4CC")
            # 右键菜单功能
            self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
            self.tableWidget.customContextMenuRequested.connect(self.showMenu)
            self.contextMenu = QMenu(self.tableWidget)
            self.cpaction = self.contextMenu.addAction('复制所选内容Ctrl+C')
            self.delaction = self.contextMenu.addAction('删除行Ctrl+D')
            self.expaction = self.contextMenu.addAction('导出全部Ctrl+E')
            self.cpaction.triggered.connect(self.table_copy)
            self.delaction.triggered.connect(self.del_row)
            self.expaction.triggered.connect(lambda: self.export(list_cols)) # 使用lambda表达式传递自定义参数
            self.tableWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)

            x = 0
            for row in results:
                for y in range(cnt_cols):
                    self.tableWidget.setItem(x, y, QTableWidgetItem(str(row[y])))
                x += 1

            resultWidgetLayout = QHBoxLayout()
            resultWidgetLayout.addWidget(self.tableWidget, Qt.AlignCenter)
            self.setLayout(resultWidgetLayout)

        except:
            QMessageBox.information(self, "提示", "请重新选择搜索条件！")

    def showMenu(self, pos):  # 右键展示菜单，pos 为鼠标位置
        # 菜单显示前，将它移动到鼠标点击的位置
        self.contextMenu.exec_(QCursor.pos())  # 在鼠标位置显示

    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_C) and QApplication.keyboardModifiers() == Qt.ControlModifier:
            # 按键事件，ctrl+c时触发，复制。
            # self.clipboard.clear()#清空剪切板，好像没啥用
            self.table_copy()
        elif (event.key() == Qt.Key_D) and QApplication.keyboardModifiers() == Qt.ControlModifier:
            # 按键事件，ctrl+d时触发，删除所在行。
            self.del_row()
        elif (event.key() == Qt.Key_E) and QApplication.keyboardModifiers() == Qt.ControlModifier:
            # 按键事件，ctrl+e时触发，导出整张表。
            self.export()
        else:
            pass

    def del_row(self):
        # 对选取的单元格进行操作，特别是删除，记得先排序，再从最大索引，往最小索引方向进行操作。
        selectRect = self.tableWidget.selectedRanges()
        set_indices = set()  # 创建空set存放需要删除的行号
        for rect in selectRect:  # 获取范围边界
            for row in range(rect.topRow(), rect.bottomRow() + 1):
                set_indices.add(row)  # 获取被选中的行号（顺序是被依次选中的顺序）
        set_indices = sorted(set_indices, reverse=True)  # 降序排列（默认升序）
        for row_idx in set_indices:
            self.tableWidget.removeRow(row_idx)  # 根据行号删除行

    def table_copy(self):
        selectRect = self.tableWidget.selectedRanges()
        self.text = str()
        for r in selectRect:  # 获取范围边界
            self.top = r.topRow()
            self.left = r.leftColumn()
            self.bottom = r.bottomRow()
            self.right = r.rightColumn()
            self.column_n = 0
            self.number = 0
            self.row_n = 0
            self.column_n = self.right - self.left + 1
            self.row_n = self.bottom - self.top + 1
            self.number = self.row_n * self.column_n
            self.c = []
            for i in range(self.number):
                self.c.append(' \t')  # 注意，是空格+\t
                if (i % self.column_n) == (self.column_n - 1):
                    self.c.append('\n')
                else:
                    pass
                # 这里生成了一个列表，大小是：行X（列+1），换行符占了一列。
                # 默认情况下，列表中全部是空格，
            self.c.pop()  # 删去最后多余的换行符

            range1 = range(self.top, self.bottom + 1)
            range2 = range(self.left, self.right + 1)
            for row, column in product(range1, range2):
                # 实现下面语句的功能
                # for row in range1:
                #    for column in range2:
                try:
                    data = self.tableWidget.item(row, column).text()
                    number2 = (row - self.top) * (self.column_n + 1) + (column - self.left)
                    self.c[number2] = data + '\t'
                    # 计算出单元格的位置，替换掉原来的空格。
                except:
                    pass
            for s in self.c:
                self.text = self.text + s
        self.clipboard.setText(self.text)
        self.text = str()  # 字符串归零

    def export(self, list_cols):
        # dir_selected = QFileDialog.getExistingDirectory(self, "选择文件夹", "./")
        path_selected = QFileDialog.getSaveFileName(self, "导出到Excel文件", "./",
                                                   "Excel文件 (*.xlsx);;All Files (*)")

        if path_selected[0] == '': # 点击“取消”时，会返回元组('', '')
            return

        save_file = path_selected[0]
        workbook = Workbook()
        worksheet = workbook.active
        # 每个workbook创建后，默认会存在一个worksheet，对默认的worksheet进行重命名
        worksheet.title = "Sheet1"
        worksheet.append(list_cols)
        row_cnt = self.tableWidget.rowCount()
        col_cnt = self.tableWidget.columnCount()
        for i in range(row_cnt):
            row = [] # 存放每行的内容
            for j in range(col_cnt):
                try:
                    data = self.tableWidget.item(i, j).text()
                    row.append(data)
                except:
                    row.append('')
            worksheet.append(row)  # 把每一行append到worksheet中
        workbook.save(filename=save_file)

    def closeEvent(self, event):
        pass
        # self.closebut_clicked.emit() # 子窗口关闭时发送信号


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sql = "SELECT date, product_id, product_name, account_id, account_type, total_value, market_value, total_cash, available_cash, holding_pnl FROM acc_equity WHERE product_id IN ('FH1','FH10','FH2','FH3','FH9','HT1','HT2','HT3','HT5','HT6','HT7','LH1','LH2','ZS1') and date_format(date,'%Y-%m-%d') >= '2021-03-01' and date_format(date,'%Y-%m-%d') <= '2021-05-11'"
    mw = SqlResultWin(sql)
    mw.show()
    app.exec_()
