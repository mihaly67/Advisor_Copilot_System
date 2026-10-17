    def add_plot(self, title=""):
        """pyqtgraph PlotWidget hozzaadasa (fallback: QLabel ha nincs pyqtgraph)."""
        if HAS_PYQTGRAPH:
            pw = pg.PlotWidget()
            pw.setBackground(COLOR_BG)
            pw.setTitle(title, color=COLOR_TEXT_DIM, size="8pt")
            pw.setMaximumHeight(80)
            pw.showGrid(x=False, y=True, alpha=0.15)
            for axis in [pw.getAxis('bottom'), pw.getAxis('left')]:
                axis.setPen(pg.mkPen(COLOR_BORDER))
                axis.setTextPen(pg.mkPen(COLOR_TEXT_DIM))
                axis.setStyle(tickLength=-3)
            self.layout_v.addWidget(pw)
            return pw
        else:
            lbl = QLabel("[pyqtgraph nem erheto el]")
            lbl.setStyleSheet("color: " + COLOR_TEXT_DIM + "; font-size: 9px;")
            self.layout_v.addWidget(lbl)
            return None
