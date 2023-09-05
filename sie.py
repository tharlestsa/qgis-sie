import re
import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QDockWidget, QPushButton, QDockWidget, \
    QGridLayout, QComboBox, QLineEdit
from PyQt5.QtCore import Qt, QTimer, QDate
from qgis.core import Qgis, QgsProject, QgsRasterLayer, QgsProject, QgsApplication, QgsCoordinateReferenceSystem, \
    QgsCoordinateTransform, QgsPointXY
from qgis.gui import QgsMapCanvas
from qgis.utils import iface
from datetime import datetime
from satsearch import Search

class Constants:
    STAC_API_URL = 'https://earth-search.aws.element84.com/v0'
    COLLECTION = 'sentinel-s2-l2a-cogs'
    CLOUD_COVER_LIMIT = 80


layerGridDockWidgetInstance = None

def copy_url_to_clipboard(layer):
    clipboard = QApplication.clipboard()
    clipboard.setText(layer.customProperty("url"))
    msg = iface.messageBar().createMessage("IMAGE TMS", "The URL of TMS was copied to clipboard.")
    iface.messageBar().pushWidget(msg, level=Qgis.Info)


class LayerGridDockWidget(QDockWidget):
    def __init__(self, layers):
        super(LayerGridDockWidget, self).__init__()

        self.setWindowTitle("Layer Grid")
        self.canvases = []

        # Create a scroll area
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)

        self.widget = QWidget()
        self.setWidget(self.widget)
        self.layout = QGridLayout()
        self.widget.setLayout(self.layout)

        self.scrollArea.setWidget(self.widget)

        self.setWidget(self.scrollArea)

        # Connect the signal
        iface.mapCanvas().extentsChanged.connect(self.sync_zoom)

        self.updateGrid(layers)

    def updateGrid(self, layers):
        try:
            sorted_layers = sorted(layers, key=lambda x: x.customProperty("date"), reverse=True)

            # Clear existing widgets from the layout
            for i in reversed(range(self.layout.count())):
                widget = self.layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()

            self.canvases = []

            # Add sorted layers to layout
            row = 0
            col = 0
            for layer in sorted_layers:
                label = QLabel(layer.name())
                label.setStyleSheet("font-size: 12px;")
                label.setAlignment(Qt.AlignCenter)
                canvas = QgsMapCanvas()
                canvas.setCanvasColor(Qt.gray)
                canvas.setExtent(layer.extent())
                canvas.setLayers([layer])

                self.canvases.append(canvas)
                copy_url_button = QPushButton('Copy URL')
                copy_url_button.clicked.connect(lambda clicked, layer=layer: copy_url_to_clipboard(layer))

                self.layout.addWidget(label, row, col)
                self.layout.addWidget(canvas, row + 1, col)
                self.layout.addWidget(copy_url_button, row + 2, col)

                col += 1
                if col > 2:
                    col = 0
                    row += 3

        except Exception as e:
            msg = iface.messageBar().createMessage("GRID", f"Error -> {e}")
            iface.messageBar().pushWidget(msg, level=Qgis.Critical)
            pass

    def sync_zoom(self):
        main_canvas = iface.mapCanvas()
        extent = main_canvas.extent()
        if self.canvases:
            for canvas in self.canvases:
                canvas.setExtent(extent)
                canvas.refresh()


class SentinelImageExplorerWidget(QWidget):
    def __init__(self):
        super(SentinelImageExplorerWidget, self).__init__()
        self.progress_message_bar = None
        self.progress_bar = None
        
        self.timer_smooth = QTimer()
        self.timer_smooth.timeout.connect(self.update_opacity)
        self.current_opacity = 1.0
        self.target_opacity = 1.0

        self.layout = QVBoxLayout()
        self.label = QLabel("")
        self.label.setStyleSheet("font-size: 25px;")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # Create a horizontal layout for the slider and buttons
        self.hbox = QHBoxLayout()
        self.hboxParams = QHBoxLayout()

        self.startLabel = QLabel("Start Date:")
        self.endLabel = QLabel("End Date:")

        # Add date filters
        self.hbox.addWidget(self.startLabel)
        self.startDateEdit = QDateEdit()
        self.startDateEdit.setDate(QDate.currentDate())
        self.startDateEdit.setCalendarPopup(True)
        self.startDateEdit.setFixedWidth(100)
        self.startDateEdit.setDisplayFormat("dd/MM/yyyy")
        self.hbox.addWidget(self.startDateEdit)

        current_date = QDate.currentDate()
        defaul_date = QDate(current_date.year(), 1, 1)
        self.startDateEdit.setDate(defaul_date)

        self.hbox.addWidget(self.endLabel)
        self.endDateEdit = QDateEdit()
        self.endDateEdit.setDate(QDate.currentDate())
        self.endDateEdit.setCalendarPopup(True)
        self.endDateEdit.setFixedWidth(100)
        self.endDateEdit.setDisplayFormat("dd/MM/yyyy")
        self.hbox.addWidget(self.endDateEdit)

        self.coordInput = QLineEdit(self)
        self.coordInput.setPlaceholderText("Point lat,lon (EPSG:4326)")
        self.hbox.addWidget(self.coordInput)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setTickInterval(1)
        self.slider.setValue(1)
        self.slider.hide()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.play_timelapse)

        self.filterButton = QPushButton("Filter")
        self.filterButton.setCursor(Qt.PointingHandCursor)
        self.filterButton.setIcon(QgsApplication.getThemeIcon('/mActionFilter.svg'))
        self.filterButton.setToolTip('Apply Date Filter')
        self.hbox.addWidget(self.filterButton)

        self.clearFilterButton = QPushButton("Clear")
        self.clearFilterButton.setIcon(QgsApplication.getThemeIcon("/mIconClearText.svg"))
        self.clearFilterButton.setCursor(Qt.PointingHandCursor)
        self.filterButton.setToolTip('Clear Date Filter')
        self.hbox.addWidget(self.clearFilterButton)

        self.playButton = QPushButton("Play")
        self.playButton.setIcon(QgsApplication.getThemeIcon("/mActionPlay.svg"))
        self.playButton.setCursor(Qt.PointingHandCursor)
        self.hbox.addWidget(self.playButton)

        self.stopButton = QPushButton("Stop")
        self.stopButton.setIcon(QgsApplication.getThemeIcon("/mActionStop.svg"))
        self.stopButton.setCursor(Qt.PointingHandCursor)
        self.hbox.addWidget(self.stopButton)

        self.gridButton = QPushButton("Grid")
        self.gridButton.setIcon(QgsApplication.getThemeIcon("/mActionNewTable.svg"))
        self.gridButton.setCursor(Qt.PointingHandCursor)
        self.hbox.addWidget(self.gridButton)

        self.removeButton = QPushButton("Remove")
        self.removeButton.setIcon(QgsApplication.getThemeIcon("/mActionFileExit.svg"))
        self.removeButton.setCursor(Qt.PointingHandCursor)
        self.hbox.addWidget(self.removeButton)

        self.collectionComboBox = QComboBox()
        self.bandsLineEdit = QLineEdit(self)
        self.colorFormulaLineEdit = QLineEdit(self)
        self.bandsLineEdit.setText("B04, B03, B02")
        self.colorFormulaLineEdit.setText("Gamma+RGB+6+Saturation+2.0+Sigmoidal+RGB+20+0.45")

        self.hboxParams.addWidget(QLabel("Collection:"))
        self.hboxParams.addWidget(self.collectionComboBox)
        self.hboxParams.addWidget(QLabel("Bands:"))
        self.hboxParams.addWidget(self.bandsLineEdit)
        self.hboxParams.addWidget(QLabel("Color Formula:"))
        self.hboxParams.addWidget(self.colorFormulaLineEdit)

        # Add the horizontal layout to the vertical layout
        self.layout.addLayout(self.hbox)
        self.layout.addLayout(self.hboxParams)
        self.layout.addWidget(self.slider)
        # Set the layout for the QWidget
        self.setLayout(self.layout)

        # Connect events
        self.removeButton.clicked.connect(self.remove_layers)
        self.playButton.clicked.connect(self.start_timelapse)
        self.stopButton.clicked.connect(self.stop_timelapse)
        self.slider.valueChanged.connect(self.slider_changed)
        self.filterButton.clicked.connect(self.filter_layers)
        self.clearFilterButton.clicked.connect(self.clear_filter)
        self.gridButton.clicked.connect(self.change_visibility_grid)

        self.setLayout(self.layout)
        self.layer_ids = []
        self.current_layer_id = None
        self.current_layer_name = None
        self.images = []
        self.fetch_collections()

    def fetch_collections(self):
        collections_url = "https://earth-search.aws.element84.com/v0/collections"
        response = requests.get(collections_url)

        if response.status_code == 200:
            data = response.json()
            for collection in data["collections"]:
                self.collectionComboBox.addItem(collection["id"])
        
        self.collectionComboBox.setCurrentText("sentinel-s2-l2a-cogs")
        
    def fetch_images(self):
        try:
            self.images = self.search_image()
            self.init()

        except Exception as e:
            print(f"Error Searching Images: {e}")
            pass

    def search_image(self):
        try:
            self.start_processing()
            coord_text = self.coordInput.text()
            if coord_text is None or coord_text.strip() == "":
                msg = iface.messageBar().createMessage("S2_SEARCH", "You need to inform lat and lon.")
                iface.messageBar().pushWidget(msg, level=Qgis.Critical)
                self.finish_progress()
                return
            self.update_progress(5)
            selected_collection = self.collectionComboBox.currentText()
            bands_text = self.bandsLineEdit.text()
            bands_list = bands_text.replace(" ", "").split(",")
            self.update_progress(10)

            bands = "&".join([f"assets={band}" for band in bands_list])
            color_formula = self.colorFormulaLineEdit.text()
            lat, lon = map(float, coord_text.split(','))

            self.update_progress(13)

            geometry = {"type": "Point", "coordinates": [lon, lat]}

            start_date = self.startDateEdit.date()
            end_date = self.endDateEdit.date()

            iso_start_date = f"{start_date.year()}-{start_date.month():02d}-{start_date.day():02d}"
            iso_end_date = f"{end_date.year()}-{end_date.month():02d}-{end_date.day():02d}"

            self.update_progress(16)

            date_range = f"{iso_start_date}/{iso_end_date}"
            search = Search(url=Constants.STAC_API_URL,
                            intersects=geometry,
                            datetime=date_range,
                            collections=[Constants.COLLECTION],
                            query={'eo:cloud_cover': {'lt': Constants.CLOUD_COVER_LIMIT}})

            items = sorted(search.items(), key=lambda item: item.properties['eo:cloud_cover'])

            self.update_progress(30)

            total_images = len(items)
            progress_per_image = 100.0 / total_images

            images = []

            for i, item in enumerate(items):
                date_string = re.search(r'\d{8}', item.id).group()
                date = datetime.strptime(date_string, '%Y%m%d')
                name = date.strftime('%d/%m/%Y')
                url = f"https://titiler.xyz/stac/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}@1x?url={Constants.STAC_API_URL}/collections/{selected_collection}/items/{item.id}&{bands}&color_formula={color_formula}"
                images.append({
                    "id": item.id,
                    "name": f"{selected_collection.upper()} - {name}",
                    "date": date,
                    "url": url
                })
                self.update_progress(5 + (i + 1) * progress_per_image)

            self.finish_progress()
            self.images = images
        except Exception as e:
            self.finish_progress()
            msg = iface.messageBar().createMessage("S2_SEARCH", f"Error Searching Images -> {e}")
            iface.messageBar().pushWidget(msg, level=Qgis.Critical)
            pass

    def init(self):
        # Sort mosaics by date in descending order (most recent first)
        self.images.sort(key=lambda x: x['date'], reverse=True)

        self.slider.setMinimum(1)
        self.slider.setMaximum(len(self.images))

        # Initialize layers (assuming they are already added)
        self.layer_ids = []

        for image in self.images:
            layer_id = self.add_layer(image)
            if layer_id:
                self.layer_ids.append(layer_id)

        # Initially, make the first layer visible
        self.current_layer_id = self.layer_ids[0]
        self.label.setText(f"{self.images[0]['name']}")
        self.label.setStyleSheet("font-size: 25px;")
        QgsProject.instance().layerTreeRoot().findLayer(
            self.current_layer_id
        ).setItemVisibilityChecked(True)

    def add_layer(self, image):
        tile_url = image['url']
        service_url = tile_url.replace('=', '%3D').replace('&', '%26')

        qgis_tms_uri = 'type=xyz&zmin={0}&zmax={1}&url={2}'.format(
            8, 14, service_url
        )

        layer = QgsRasterLayer(qgis_tms_uri, image['name'], 'wms')
        layer.setCustomProperty("id", image['id'])
        layer.setCustomProperty("date", image['date'])
        layer.setCustomProperty("url", image['url'])

        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            QgsProject.instance().layerTreeRoot().findLayer(layer).setItemVisibilityChecked(False)
            return layer.id()

        return None

    def zoom_to_point(self):
        coord_text = self.coordInput.text()
        lat, lon = map(float, coord_text.split(','))

        # Convert from EPSG:4326 to EPSG:3857
        source_crs = QgsCoordinateReferenceSystem(4326)
        dest_crs = QgsCoordinateReferenceSystem(3857)
        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())  # Include project instance

        point_4326 = QgsPointXY(lon, lat)
        point_3857 = transform.transform(point_4326)

        # Assuming iface.mapCanvas() returns the map canvas
        canvas = iface.mapCanvas()
        canvas.setCenter(point_3857)
        canvas.zoomScale(100000)
        canvas.refresh()

    def filter_layers(self):
        self.slider.hide()
        self.search_image()

        if len(self.images) == 0:
            msg = iface.messageBar().createMessage("FILTER", "No result found for the selected date range or point.")
            iface.messageBar().pushWidget(msg, level=Qgis.Critical)
            return

        # Update the slider's maximum value based on the filtered list
        self.slider.setMaximum(len(self.images) - 1)

        # Remove existing layers and re-initialize based on filtered data
        self.remove_layers()
        self.init()

        coord = self.coordInput.text()
        if coord:
            self.zoom_to_point()

        self.slider.show()

    def clear_filter(self):
        # Resetting the date filters to their initial state
        self.startDateEdit.setDate(QDate.currentDate())
        self.endDateEdit.setDate(QDate.currentDate())

        self.remove_layers()

        # Fetch the mosaics again
        self.filter_layers()

    def remove_layers(self):
        for layer_id in self.layer_ids:
            QgsProject.instance().removeMapLayer(layer_id)
        self.layer_ids.clear()

    def start_timelapse(self):
        self.timer.start(1200)

    def stop_timelapse(self):
        self.timer.stop()
        self.timer_smooth.stop()

    def play_timelapse(self):
        current_value = self.slider.value()
        if current_value >= self.slider.maximum():
            self.slider.setValue(self.slider.minimum())
        else:
            self.slider.setValue(current_value + 1)

    def slider_changed(self):
        try:
            index = self.slider.value() - 1
            # Hide the previous layer by reducing opacity
            self.target_opacity = 0.0
            self.timer_smooth.start(50)  # Update every 50ms

            # Hide the previous layer
            if self.current_layer_id:
                QgsProject.instance().layerTreeRoot().findLayer(
                    self.current_layer_id
                ).setItemVisibilityChecked(False)

            # Show the current layer
            self.current_layer_id = self.layer_ids[index]
            layer = QgsProject.instance().layerTreeRoot().findLayer(self.current_layer_id)
            layer.setItemVisibilityChecked(True)
            
            self.target_opacity = 1.0
            self.timer_smooth.start(50)  # Update every 50ms
            
            self.label.setText(f"{layer.name()}")
            self.label.setStyleSheet("font-size: 25px;")
        except Exception as e:
            self.finish_progress()
            msg = iface.messageBar().createMessage("SLIDER", f"Error  -> {e}")
            iface.messageBar().pushWidget(msg, level=Qgis.Critical)
            pass

    def change_visibility_grid(self):
        global layerGridDockWidgetInstance
        layers = list(QgsProject.instance().mapLayers().values())
        layers_with_date = [lay for lay in layers if lay.customProperty("date") is not None]

        # If the dock widget has not been created yet, create it
        if layerGridDockWidgetInstance is None:
            layerGridDockWidgetInstance = LayerGridDockWidget(layers_with_date)
            iface.addDockWidget(Qt.RightDockWidgetArea, layerGridDockWidgetInstance)
        else:
            # If it already exists, simply update its grid content
            layerGridDockWidgetInstance.updateGrid(layers_with_date)

        layerGridDockWidgetInstance.show()
        
    def update_opacity(self):
        try:
            if abs(self.current_opacity - self.target_opacity) < 0.1:
                self.timer_smooth.stop()
                return
            
            if self.current_opacity < self.target_opacity:
                self.current_opacity += 0.1  # increment opacity
            elif self.current_opacity > self.target_opacity:
                self.current_opacity -= 0.1  # decrement opacity

            layer = QgsProject.instance().mapLayer(self.current_layer_id)
            layer.setOpacity(self.current_opacity * 100)  # setOpacity expects percentages
            layer.triggerRepaint()
        except Exception as e:
            self.finish_progress()
            msg = iface.messageBar().createMessage("OPACITY", f"Error -> {e}")
            iface.messageBar().pushWidget(msg, level=Qgis.Critical)
            pass
        
    def start_processing(self):
        # Remove existing progress bar if any
        if self.progress_message_bar:
            self.finish_progress()

        self.progress_message_bar = iface.messageBar().createMessage("")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)

        # Create a QWidget to hold the progress bar
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Processing..."))
        layout.addWidget(self.progress_bar)
        container.setLayout(layout)

        self.progress_message_bar.layout().addWidget(container)
        iface.messageBar().pushWidget(self.progress_message_bar, Qgis.Info)

    def update_progress(self, value):
        if self.progress_bar:
            self.progress_bar.setValue(value)
        else:
            self.start_processing()
            self.progress_bar.setValue(value)

    def finish_progress(self):
        if self.progress_message_bar:
            # Hide and remove the progress bar
            iface.messageBar().clearWidgets()
            self.progress_bar = None
            self.progress_message_bar = None


# Instantiate the widget
sentinel_image_explorer_widget = SentinelImageExplorerWidget()

# Wrap the widget in a QDockWidget
dock = QDockWidget("Sentinel Image Explorer (SIE)")
dock.setWidget(sentinel_image_explorer_widget)

# Add the QDockWidget to the QGIS interface at the top
iface.addDockWidget(Qt.TopDockWidgetArea, dock)
