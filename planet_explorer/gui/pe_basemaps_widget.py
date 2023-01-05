# -*- coding: utf-8 -*-
"""
***************************************************************************
    pe_basemaps_widget.py
    ---------------------
    Date                 : August 2020
    Author               : Planet Federal
    Copyright            : (C) 2017 Boundless, http://boundlessgeo.com
                         : (C) 2019 Planet Inc, https://planet.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
__author__ = "Planet Federal"
__date__ = "August 2020"
__copyright__ = "(C) 2019 Planet Inc, https://planet.com"

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = "$Format:%H$"

import math
import os

from planet.api.exceptions import InvalidAPIKey
from planet.api.models import MosaicQuads, Mosaics
from qgis.PyQt import QtCore
from qgis.PyQt.QtCore import QObject, QThread, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QImage, QPixmap
from qgis.PyQt.QtNetwork import QNetworkAccessManager, QNetworkRequest
from qgis.PyQt.QtWidgets import QApplication, QMessageBox, QVBoxLayout
from qgis.core import Qgis, QgsDistanceArea, QgsGeometry, QgsRectangle, QgsUnitTypes
from qgis.PyQt import uic

from ..pe_analytics import (
    analytics_track,
    BASEMAP_SERVICE_ADDED_TO_MAP,
    BASEMAP_SERVICE_CONNECTION_ESTABLISHED,
    BASEMAP_COMPLETE_ORDER,
    BASEMAP_PARTIAL_ORDER,
)

from ..pe_utils import (
    INTERVAL,
    LINKS,
    NAME,
    QUADS_AOI_COLOR,
    add_mosaics_to_qgis_project,
    date_interval_from_mosaics,
    mosaic_title,
    open_link_with_browser,
)
from ..planet_api import PlanetClient
from ..planet_api.p_quad_orders import (
    create_quad_order_from_mosaics,
    create_quad_order_from_quads,
)
from .pe_basemap_layer_widget import BasemapRenderingOptionsWidget
from .pe_basemaps_list_widget import BasemapsListWidget
from .pe_filters import PlanetAOIFilter
from .pe_gui_utils import waitcursor
from .pe_orders_monitor_dockwidget import refresh_orders, show_orders_monitor
from .pe_quads_treewidget import QuadsTreeWidget

ID = "id"
SERIES = "series"
THUMB = "thumb"
BBOX = "bbox"
DATATYPE = "datatype"
PRODUCT_TYPE = "product_type"
TIMELAPSE = "timelapse"

QUADS_PER_PAGE = 50
MAX_QUADS_TO_DOWNLOAD = 100
MAX_AREA_TO_DOWNLOAD = 100000

# =========================================================== CAN BE MOVED
GROUP_NAME = 'name'
GROUP_KEYS = 'keys'

GROUP_ALL = {
    GROUP_NAME: 'All',
    GROUP_KEYS: []
}
GROUP_OTHER = {
    GROUP_NAME: 'Other',
    GROUP_KEYS: []
}

GROUP_AFGHANISTAN = {
    GROUP_NAME: 'Afghanistan',
    GROUP_KEYS: ['afghanistan', 'nangarhar']
}
GROUP_ROADS_AND_BUILDINGS = {
    GROUP_NAME: 'Roads and buildings',
    GROUP_KEYS: ['roads and buildings', 'road and building']
}
GROUP_ANALYTICS = {
    GROUP_NAME: 'Analytics',
    GROUP_KEYS: ['analytics', 'analytic']
}
GROUP_OCEAN = {
    GROUP_NAME: 'Ocean',
    GROUP_KEYS: [
        'andaman sea',
        'indian ocean',
        'south pacific reef',
        'coral sea',
        'hawaii reef',
        'mesoamerica reef',
        'moorea reef',
        'red sea',
        'small systems reef',
        'southwest pacific',
        'subtropical eastern reef',
        'timor sea',
        'tropical eastern pacific',
        'west indian ocean'
    ]
}
GROUP_ANZO_AGRO = {
    GROUP_NAME: 'Anzo Agro',
    GROUP_KEYS: ['anzo agro']
}
GROUP_ARCTIC = {
    GROUP_NAME: 'Arctic',
    GROUP_KEYS: ['arctic']
}
GROUP_USA = {
    GROUP_NAME: 'USA',
    GROUP_KEYS: [
        'usa',
        'usda',
        'arkansas',
        'california',
        'continental us',
        'lake guntersville',
        'maine',
        'ford basin',
        'powder river basin',
        'missouri',
        'new mexico',
        'la skysat',
        'west coast us'
    ]
}
GROUP_KENYA = {
    GROUP_NAME: 'Kenya',
    GROUP_KEYS: ['kenya']
}
GROUP_Australia = {
    GROUP_NAME: 'Australia',
    GROUP_KEYS: ['australia', 'aus', 'queensland']
}
GROUP_NEW_ZEALAND = {
    GROUP_NAME: 'New Zealand',
    GROUP_KEYS: ['new zealand', 'nz']
}
GROUP_BAYER = {
    GROUP_NAME: 'Bayer',
    GROUP_KEYS: ['bayer']
}
GROUP_INDONESIA = {
    GROUP_NAME: 'Indonesia',
    GROUP_KEYS: ['indonesia', 'berau']
}
GROUP_INDIA = {
    GROUP_NAME: 'India',
    GROUP_KEYS: ['india', 'bhatinda']
}
GROUP_GERMANY = {
    GROUP_NAME: 'Germany',
    GROUP_KEYS: ['germany', 'bkg']
}
GROUP_BULGARIA = {
    GROUP_NAME: 'Bulgaria',
    GROUP_KEYS: ['bulgaria']
}
GROUP_CAMPBELL = {
    GROUP_NAME: 'Campbell',
    GROUP_KEYS: ['campbell']
}
GROUP_Global = {
    GROUP_NAME: 'Global',
    GROUP_KEYS: ['global']
}
GROUP_CHRISTIAN = {
    GROUP_NAME: 'Christian',
    GROUP_KEYS: ['christian']
}
GROUP_COLOMBIA = {
    GROUP_NAME: 'Colombia',
    GROUP_KEYS: ['colombia']
}
GROUP_CZECHIA = {
    GROUP_NAME: 'Czechia',
    GROUP_KEYS: ['czechia']
}
GROUP_DESERT_RESEARCH_INSTITUTE = {
    GROUP_NAME: 'Desert Research Institute',
    GROUP_KEYS: ['desert research institute']
}
GROUP_AFRICA = {
    GROUP_NAME: 'Africa',
    GROUP_KEYS: ['africa']
}
GROUP_MICRONESIA = {
    GROUP_NAME: 'Micronesia',
    GROUP_KEYS: ['micronesia']
}
GROUP_SOLOMONS = {
    GROUP_NAME: 'Solomons',
    GROUP_KEYS: ['solomons']
}
GROUP_EUROPE = {
    GROUP_NAME: 'Europe',
    GROUP_KEYS: ['europe']
}
GROUP_FOREST_RESOURCE_CONSULTANTS = {
    GROUP_NAME: 'Forest resource consultants',
    GROUP_KEYS: ['forest resource consultants']
}
GROUP_FREEPORT_MCMORAN = {
    GROUP_NAME: 'Freeport McMoran',
    GROUP_KEYS: ['freeport mcmoran']
}
GROUP_GEORGIA_PACIFIC = {
    GROUP_NAME: 'Georgia Pacific',
    GROUP_KEYS: ['georgia pacific']
}
GROUP_GREEN_DIAMOND = {
    GROUP_NAME: 'Green Diamond',
    GROUP_KEYS: ['green diamond']
}
GROUP_HANCOCK = {
    GROUP_NAME: 'Hancock',
    GROUP_KEYS: ['hancock']
}
GROUP_HUDBAY = {
    GROUP_NAME: 'Hudbay',
    GROUP_KEYS: ['hudbay']
}
GROUP_HUMBOLT = {
    GROUP_NAME: 'Humbolt',
    GROUP_KEYS: ['humbolt']
}
GROUP_WEATHER = {
    GROUP_NAME: 'Weather',
    GROUP_KEYS: ['weather', 'hurricane', 'cyclone']
}
GROUP_HYDRO_ENGINEERING = {
    GROUP_NAME: 'Hydro Engineering',
    GROUP_KEYS: ['hydro engineering']
}
GROUP_SYRACUSE = {
    GROUP_NAME: 'Syracuse',
    GROUP_KEYS: ['syracuse']
}
GROUP_IMAGESAT = {
    GROUP_NAME: 'ImageSat',
    GROUP_KEYS: ['imagesat']
}
GROUP_IROGUOIS = {
    GROUP_NAME: 'Iroguois',
    GROUP_KEYS: ['iroguois']
}
GROUP_JAPAN = {
    GROUP_NAME: 'Japan',
    GROUP_KEYS: ['japan']
}
GROUP_JDAVIS_ROLLING = {
    GROUP_NAME: 'JDavis Rolling',
    GROUP_KEYS: ['jdavis rolling']
}
GROUP_CANADA = {
    GROUP_NAME: 'Canada',
    GROUP_KEYS: [
        'alberta',
        'manitoba',
        'brunswick',
        'nova scotia',
        'saskatchewan'
    ]
}
GROUP_KARI = {
    GROUP_NAME: 'Kari',
    GROUP_KEYS: ['kari']
}
GROUP_LANGDALE_FOREST = {
    GROUP_NAME: 'Langdale Forest',
    GROUP_KEYS: ['langdale forest']
}
GROUP_BRAZIL = {
    GROUP_NAME: 'Brazil',
    GROUP_KEYS: ['brazil']
}
GROUP_MEDRES = {
    GROUP_NAME: 'Medres',
    GROUP_KEYS: ['medres']
}
GROUP_NAGURSKOVE = {
    GROUP_NAME: 'Nagurskove',
    GROUP_KEYS: ['nagurskove']
}
GROUP_MALI = {
    GROUP_NAME: 'Mali',
    GROUP_KEYS: ['mali']
}
GROUP_NORWAY = {
    GROUP_NAME: 'Norway',
    GROUP_KEYS: ['norway']
}
GROUP_ASIA = {
    GROUP_NAME: 'Asia',
    GROUP_KEYS: [
        'asia',
        'china',
        'indonesia',
        'india',
        'taiwan',
        'japan'
    ]
}
GROUP_CARIBBEAN = {
    GROUP_NAME: 'Caribbean',
    GROUP_KEYS: ['caribbean']
}
GROUP_ARABIAN = {
    GROUP_NAME: 'Arabian',
    GROUP_KEYS: ['arabian']
}
GROUP_ONE_SOIL_NETHERLANDS = {
    GROUP_NAME: 'One soil Netherlands',
    GROUP_KEYS: ['one soil netherlands']
}
GROUP_PERU = {
    GROUP_NAME: 'Peru',
    GROUP_KEYS: ['peru']
}
GROUP_PLATEL = {
    GROUP_NAME: 'Platel',
    GROUP_KEYS: ['platel']
}
GROUP_POINT_REYES = {
    GROUP_NAME: 'Point Reyes',
    GROUP_KEYS: ['point reyes']
}
GROUP_PROGEA = {
    GROUP_NAME: 'ProGea',
    GROUP_KEYS: ['progea']
}
GROUP_PLANETSCOPE = {
    GROUP_NAME: 'PlanetScope',
    GROUP_KEYS: ['planetscope', 'ps analytic']
}
GROUP_RAYONIER_ADV_MATERIALS = {
    GROUP_NAME: 'Rayonier Adv Materials',
    GROUP_KEYS: ['rayonier adv materials']
}
GROUP_SALO_AI = {
    GROUP_NAME: 'Salo AI',
    GROUP_KEYS: ['salo ai']
}
GROUP_SAN_LUIS_RESERVOIR = {
    GROUP_NAME: 'San Luis Reservoir',
    GROUP_KEYS: ['san luis reservoir']
}
GROUP_BELIZE = {
    GROUP_NAME: 'Belize',
    GROUP_KEYS: ['belize']
}
GROUP_SAUGAHATCHEE = {
    GROUP_NAME: 'Saugahatchee',
    GROUP_KEYS: ['saugahatchee']
}
GROUP_SERBIA = {
    GROUP_NAME: 'Serbia',
    GROUP_KEYS: ['serbia', 'serbian']
}
GROUP_SETTONG_FARMS = {
    GROUP_NAME: 'Settong Farms',
    GROUP_KEYS: ['settong farms']
}
GROUP_SIF = {
    GROUP_NAME: 'SIF',
    GROUP_KEYS: ['sif']
}
GROUP_SILVICS = {
    GROUP_NAME: 'Silvics',
    GROUP_KEYS: ['silvics']
}
GROUP_SIME_DARBY = {
    GROUP_NAME: 'Sime Darby',
    GROUP_KEYS: ['sime darby']
}
GROUP_SOUTH_AMERICA = {
    GROUP_NAME: 'South America',
    GROUP_KEYS: ['south america']
}
GROUP_CHINA = {
    GROUP_NAME: 'China',
    GROUP_KEYS: ['china']
}
GROUP_STANFORD_ARCHIVE = {
    GROUP_NAME: 'Stanford Archive',
    GROUP_KEYS: ['stanford archive']
}
GROUP_SUPERDOVE = {
    GROUP_NAME: 'Superdove',
    GROUP_KEYS: ['superdove']
}
GROUP_TAIWAN = {
    GROUP_NAME: 'Taiwan',
    GROUP_KEYS: ['taiwan']
}
GROUP_TUNISIA = {
    GROUP_NAME: 'Tunisia',
    GROUP_KEYS: ['tunisia']
}
GROUP_UNITED_ARAB_EMIRATES = {
    GROUP_NAME: 'United Arab Emirates',
    GROUP_KEYS: ['united arab emirates']
}
GROUP_UKRAINE = {
    GROUP_NAME: 'Ukraine',
    GROUP_KEYS: ['ukraine']
}
GROUP_URUGAUY = {
    GROUP_NAME: 'Urugauy',
    GROUP_KEYS: ['urugauy']
}
GROUP_WAYERHAEUSER = {
    GROUP_NAME: 'Waygaeuser',
    GROUP_KEYS: ['waygaeuser']
}
GROUP_WV_QUANTUM = {
    GROUP_NAME: 'WV Quantum',
    GROUP_KEYS: ['wv quantum']
}
GROUP_ZEP_RE = {
    GROUP_NAME: 'Zep-RE',
    GROUP_KEYS: ['zep-re']
}

LIST_BASEMAP_GROUPS = [
    GROUP_AFGHANISTAN,
    GROUP_ROADS_AND_BUILDINGS,
    GROUP_ANALYTICS,
    GROUP_OCEAN,
    GROUP_ANZO_AGRO,
    GROUP_ARCTIC,
    GROUP_USA,
    GROUP_KENYA,
    GROUP_Australia,
    GROUP_NEW_ZEALAND,
    GROUP_BAYER,
    GROUP_INDONESIA,
    GROUP_INDIA,
    GROUP_GERMANY,
    GROUP_BULGARIA,
    GROUP_CAMPBELL,
    GROUP_Global,
    GROUP_CHRISTIAN,
    GROUP_COLOMBIA,
    GROUP_CZECHIA,
    GROUP_DESERT_RESEARCH_INSTITUTE,
    GROUP_AFRICA,
    GROUP_MICRONESIA,
    GROUP_SOLOMONS,
    GROUP_EUROPE,
    GROUP_FOREST_RESOURCE_CONSULTANTS,
    GROUP_FREEPORT_MCMORAN,
    GROUP_GEORGIA_PACIFIC,
    GROUP_GREEN_DIAMOND,
    GROUP_HANCOCK,
    GROUP_HUDBAY,
    GROUP_HUMBOLT,
    GROUP_WEATHER,
    GROUP_HYDRO_ENGINEERING,
    GROUP_SYRACUSE,
    GROUP_IMAGESAT,
    GROUP_IROGUOIS,
    GROUP_JAPAN,
    GROUP_JDAVIS_ROLLING,
    GROUP_CANADA,
    GROUP_KARI,
    GROUP_LANGDALE_FOREST,
    GROUP_BRAZIL,
    GROUP_MEDRES,
    GROUP_NAGURSKOVE,
    GROUP_MALI,
    GROUP_NORWAY,
    GROUP_ASIA,
    GROUP_CARIBBEAN,
    GROUP_ARABIAN,
    GROUP_ONE_SOIL_NETHERLANDS,
    GROUP_PERU,
    GROUP_PLATEL,
    GROUP_POINT_REYES,
    GROUP_PROGEA,
    GROUP_PLANETSCOPE,
    GROUP_RAYONIER_ADV_MATERIALS,
    GROUP_SALO_AI,
    GROUP_SAN_LUIS_RESERVOIR,
    GROUP_BELIZE,
    GROUP_SAUGAHATCHEE,
    GROUP_SERBIA,
    GROUP_SETTONG_FARMS,
    GROUP_SIF,
    GROUP_SILVICS,
    GROUP_SIME_DARBY,
    GROUP_SOUTH_AMERICA,
    GROUP_CHINA,
    GROUP_STANFORD_ARCHIVE,
    GROUP_SUPERDOVE,
    GROUP_TAIWAN,
    GROUP_TUNISIA,
    GROUP_UNITED_ARAB_EMIRATES,
    GROUP_UKRAINE,
    GROUP_URUGAUY,
    GROUP_WAYERHAEUSER,
    GROUP_WV_QUANTUM,
    GROUP_ZEP_RE
]

PLACEHOLDER_THUMB = ":/plugins/planet_explorer/thumb-placeholder-128.svg"

plugin_path = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(plugin_path, "ui", "basemaps_widget.ui"),
    from_imports=True,
    import_from=os.path.basename(plugin_path),
    resource_suffix="",
)


class BasemapsWidget(BASE, WIDGET):
    def __init__(self, parent):
        super(BasemapsWidget, self).__init__(parent)

        self.parent = parent

        self.p_client = PlanetClient.getInstance()

        self._series = None
        self._initialized = False
        self._quads = None

        self.oneoff = None

        self.setupUi(self)

        self.mosaicsList = BasemapsListWidget()
        self.frameResults.layout().addWidget(self.mosaicsList)
        self.mosaicsList.setVisible(False)
        self.mosaicsList.basemapsSelectionChanged.connect(self.selection_changed)

        self.quadsTree = QuadsTreeWidget()
        self.quadsTree.quadsSelectionChanged.connect(self.quads_selection_changed)
        self.grpBoxQuads.layout().addWidget(self.quadsTree)

        self.renderingOptions = BasemapRenderingOptionsWidget()
        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.renderingOptions)
        self.frameRenderingOptions.setLayout(layout)

        self.aoi_filter = PlanetAOIFilter(self, self.parent, QUADS_AOI_COLOR)
        self.grpBoxAOI.layout().addWidget(self.aoi_filter)

        self.radioDownloadComplete.setChecked(True)

        self.buttons = [self.btnOneOff, self.btnSeries, self.btnAll]

        self.btnOneOff.clicked.connect(lambda: self.btn_filter_clicked(self.btnOneOff))
        self.btnSeries.clicked.connect(lambda: self.btn_filter_clicked(self.btnSeries))
        self.btnAll.clicked.connect(lambda: self.btn_filter_clicked(self.btnAll))

        self.btnOrder.clicked.connect(self.order)
        self.btnExplore.clicked.connect(self.explore)
        self.btnCancelQuadSearch.clicked.connect(self.cancel_quad_search)

        self.btnNextOrderMethodPage.clicked.connect(self.next_order_method_page_clicked)
        self.btnBackOrderMethodPage.clicked.connect(
            lambda: self.stackedWidget.setCurrentWidget(self.searchPage)
        )
        self.btnBackAOIPage.clicked.connect(self.back_aoi_page_clicked)
        self.btnBackNamePage.clicked.connect(self.back_name_page_clicked)
        self.btnBackStreamingPage.clicked.connect(self.back_streaming_page_clicked)
        self.btnBackQuadsPage.clicked.connect(self.back_quads_page_clicked)
        self.btnNextQuadsPage.clicked.connect(self.next_quads_page_clicked)
        self.btnFindQuads.clicked.connect(self.find_quads_clicked)
        self.btnSubmitOrder.clicked.connect(self.submit_button_clicked)
        self.btnCloseConfirmation.clicked.connect(self.close_aoi_page)
        self.btnSubmitOrderStreaming.clicked.connect(
            self.submit_streaming_button_clicked
        )
        self.chkMinZoomLevel.stateChanged.connect(self.min_zoom_level_checked)
        self.chkMaxZoomLevel.stateChanged.connect(self.max_zoom_level_checked)

        levels = [str(x) for x in range(19)]
        self.comboMinZoomLevel.addItems(levels)
        self.comboMaxZoomLevel.addItems(levels)
        self.comboMaxZoomLevel.setCurrentIndex(len(levels) - 1)

        self.textBrowserOrderConfirmation.setOpenExternalLinks(False)
        self.textBrowserOrderConfirmation.anchorClicked.connect(show_orders_monitor)
        self.comboSeriesName.currentIndexChanged.connect(self.serie_selected)
        self.grpBoxFilter.collapsedStateChanged.connect(self.collapse_state_changed)
        self.lblSelectAllMosaics.linkActivated.connect(
            self.batch_select_mosaics_clicked
        )
        self.lblSelectAllQuads.linkActivated.connect(self.batch_select_quads_clicked)
        self.chkGroupByQuad.stateChanged.connect(self._populate_quads)
        self.chkOnlySRBasemaps.stateChanged.connect(self._only_sr_basemaps_changed)
        self.btnBasemapsFilter.clicked.connect(self._apply_filter)

        self.comboCadence.currentIndexChanged.connect(self.cadence_selected)
        self.comboGroup.currentIndexChanged.connect(self.group_selected)

        self.textBrowserNoAccess.setOpenLinks(False)
        self.textBrowserNoAccess.setOpenExternalLinks(False)
        self.textBrowserNoAccess.anchorClicked.connect(self._open_basemaps_website)

    def _open_basemaps_website(self):
        open_link_with_browser("https://www.planet.com/purchase")

    def init(self):
        if not self._initialized:
            self.populate_groups()
            if self.series():
                self.stackedWidget.setCurrentWidget(self.searchPage)
                self.btnSeries.setChecked(True)
                self.btn_filter_clicked(self.btnSeries)
                self._initialized = True
            else:
                self.stackedWidget.setCurrentWidget(self.noBasemapsAccessPage)
                self._initialized = True

    def reset(self):
        self._initialized = False

    def batch_select_mosaics_clicked(self, url="all"):
        checked = url == "all"
        self.mosaicsList.setAllChecked(checked)

    def batch_select_quads_clicked(self, url="all"):
        checked = url == "all"
        self.quadsTree.setAllChecked(checked)

    def collapse_state_changed(self, collapsed):

        print('collapse state changed')

        if not collapsed:
            self.set_filter_visibility()

    def set_filter_visibility(self):

        print('set filter visi')

        is_one_off = self.btnOneOff.isChecked()
        if is_one_off:
            self.grpBoxFilter.setVisible(False)
            mosaics = self.one_off_mosaics()
            self.mosaicsList.populate(mosaics)
            self.mosaicsList.setVisible(True)
            self.toggle_select_basemap_panel(False)
        else:
            is_all = self.btnAll.isChecked()
            self.grpBoxFilter.setVisible(True)
            self.labelBasemapsFilter.setVisible(is_all)
            self.textBasemapsFilter.setVisible(is_all)
            self.btnBasemapsFilter.setVisible(is_all)
            self.labelCadence.setVisible(not is_all)
            self.comboCadence.setVisible(not is_all)
            self.comboSeriesName.clear()
            if is_all:
                self.textBasemapsFilter.setText("")
                self.comboSeriesName.addItem(
                    "Apply a filter to populate this list of series", None
                )
            else:
                cadences = list(set([s[INTERVAL] for s in self.series()]))
                self.comboCadence.blockSignals(True)
                self.comboCadence.clear()
                self.comboCadence.addItem("All", None)

                def cadenceKey(c):
                    tokens = c.split(" ")
                    try:
                        i = int(tokens[0])
                        if tokens[-1].startswith("day"):
                            pass
                        elif tokens[-1].startswith("mon"):
                            i *= 30
                        else:
                            i *= 365
                        return i
                    except Exception:
                        return 1000

                cadences.sort(key=cadenceKey)
                for cadence in cadences:
                    self.comboCadence.addItem(cadence, cadence)
                self.comboCadence.blockSignals(False)
                self.cadence_selected()

    def btn_filter_clicked(self, selectedbtn):
        for btn in self.buttons:
            if btn != selectedbtn:
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.setEnabled(True)
                btn.blockSignals(False)
            selectedbtn.setEnabled(False)
        self.populate(selectedbtn)

    @waitcursor
    def series(self):

        print('series')

        if self._series is None:
            self._series = []
            response = self.p_client.list_mosaic_series()
            for page in response.iter():
                self._series.extend(page.get().get(SERIES))

            for series in self._series:
                series_name = series.get('name').lower()
                groups_to_add = []
                for basemap_group in LIST_BASEMAP_GROUPS:
                    group_name = basemap_group.get(GROUP_NAME)
                    group_keys = basemap_group.get(GROUP_KEYS)
                    for group_key in group_keys:
                        if group_key in series_name:
                            groups_to_add.append(group_name)
                            break

                if len(groups_to_add) == 0:
                    # If a series has not been assigned it is assigned to 'Other'
                    series['series_group'] = ['Other']
                else:
                    series['series_group'] = groups_to_add

            print(str(self._series))

        return self._series

    def _apply_filter(self):

        print('apply filter')

        text = self.textBasemapsFilter.text()
        mosaics = self._get_filtered_mosaics(text)
        series = self._get_filtered_series(text)
        if len(mosaics) == 0 and len(series) == 0:
            self.parent.show_message(
                "No results for current filter", level=Qgis.Warning, duration=10
            )
            return
        self.comboSeriesName.clear()
        self.comboSeriesName.addItem("Select a series or mosaic", None)
        for m in mosaics:
            self.comboSeriesName.addItem(m[NAME], (m, False))

            #print('apply filter mosaic: ' + str(m[NAME]))

        self.comboSeriesName.insertSeparator(len(mosaics))
        for s in series:

            #print('apply filter series: ' + s[NAME])

            self.comboSeriesName.addItem(s[NAME], (s, True))

    def _get_filtered_mosaics(self, text):
        mosaics = []
        response = self.p_client.get_mosaics(text)
        for page in response.iter():
            mosaics.extend(page.get().get(Mosaics.ITEM_KEY))
        mosaics = [m for m in mosaics if m[PRODUCT_TYPE] != TIMELAPSE]
        return mosaics

    def _get_filtered_series(self, text):
        return self.p_client.list_mosaic_series(text).get()[SERIES]

    def _only_sr_basemaps_changed(self):
        self.mosaicsList.set_only_sr_basemaps(self.chkOnlySRBasemaps.isChecked())

    def cadence_selected(self):

        print('cadence selected')

        cadence = self.comboCadence.currentData()
        self.comboSeriesName.blockSignals(True)
        self.comboSeriesName.clear()
        self.comboSeriesName.addItem("Select a series", None)
        series = self.series_for_interval(cadence)

        series = self.series_for_group(series)

        for s in series:

            #print(str(s))

            self.comboSeriesName.addItem(s[NAME], (s, True))
        self.comboSeriesName.blockSignals(False)
        self.toggle_select_basemap_panel(True)

    def group_selected(self):
        print('group selected')

    def populate_groups(self):

        print('populate groups')

        # Group 'All' always first in the list
        self.comboGroup.addItem(GROUP_ALL.get(GROUP_NAME))

        # Sorts the groups according to name
        list_group_names = list(map(lambda x: x[GROUP_NAME], LIST_BASEMAP_GROUPS))
        list_group_names_sorted = sorted(list_group_names)

        for group in list_group_names_sorted:
            # Adds each group name to the UI
            self.comboGroup.addItem(group)

        # Add the 'Other' group at the end of the list
        self.comboGroup.addItem(GROUP_OTHER.get(GROUP_NAME))


    def populate(self, category_btn=None):

        print('populate')

        category_btn = category_btn or self.btnAll

        self.mosaicsList.clear()
        self.btnOrder.setText("Order (0 instances)")
        self.set_filter_visibility()

        self.batch_select_mosaics_clicked("none")

    def toggle_select_basemap_panel(self, show):
        self.lblSelectBasemapName.setVisible(show)
        self.lblSelectAllMosaics.setVisible(not show)
        self.lblCheckInstances.setVisible(not show)
        self.mosaicsList.setVisible(not show)

    def min_zoom_level_checked(self):
        self.comboMinZoomLevel.setEnabled(self.chkMinZoomLevel.isChecked())

    def max_zoom_level_checked(self):
        self.comboMaxZoomLevel.setEnabled(self.chkMaxZoomLevel.isChecked())

    @waitcursor
    def one_off_mosaics(self):
        if self.oneoff is None:
            all_mosaics = []
            response = self.p_client.get_mosaics()
            for page in response.iter():
                all_mosaics.extend(page.get().get(Mosaics.ITEM_KEY))
            self.oneoff = [m for m in all_mosaics if m[PRODUCT_TYPE] != TIMELAPSE]

        return self.oneoff

    def series_for_interval(self, interval):
        series = []
        for s in self.series():
            interv = s.get(INTERVAL)
            if interv == interval or interval is None:
                series.append(s)
        return series

    def series_for_group(self, series):
        selected_group = self.comboGroup.currentText()

        if selected_group == 'All':
            return series
        else:
            print('not all')
            grouped_list = []
            for s in series:
                series_name = s[NAME]
                if self.series_in_group(selected_group, series_name):
                    grouped_list.append(s)

            return grouped_list

    def series_in_group(self, group, series_name):
        # ==================================================================== Rather add other property to the series which stores the group
        if group == 'Afghanistan':
            if series_name.startswith('Afghanistan'):
                return True
        elif group == 'Roads and buildings':
            if 'road and building' in series_name:
                return True
        elif group == 'Analytics':
            if series_name.startswith('Analytics'):
                return True
        elif group == 'Ocean':
            if 'Andaman Sea' in series_name:
                return True
        elif group == 'Anzo Agro':
            if series_name.startswith('Anzo Agro'):
                return True
        elif group == 'Arctic':
            if series_name.startswith('Arctic'):
                return True


    @waitcursor
    def mosaics_for_serie(self, serie):
        mosaics = self.p_client.get_mosaics_for_series(serie[ID])
        all_mosaics = []
        for page in mosaics.iter():
            all_mosaics.extend(page.get().get(Mosaics.ITEM_KEY))
        return all_mosaics

    def serie_selected(self):
        self.mosaicsList.clear()
        data = self.comboSeriesName.currentData()
        self.toggle_select_basemap_panel(data is None)
        self.mosaicsList.setVisible(data is not None)
        if data:
            if data[1]:  # it is a series, not a single mosaic
                try:
                    mosaics = self.mosaics_for_serie(data[0])
                except InvalidAPIKey:
                    self.parent.show_message(
                        "Insufficient privileges. Cannot show mosaics of the selected"
                        " series",
                        level=Qgis.Warning,
                        duration=10,
                    )
                    return
            else:
                mosaics = [data[0]]
            self.mosaicsList.populate(mosaics)

    def selection_changed(self):
        selected = self.mosaicsList.selected_mosaics()
        n = len(selected)
        self.btnOrder.setText(f"Order ({n} items)")

    def quads_selection_changed(self):
        selected = self.quadsTree.selected_quads()
        n = len(selected)
        total = self.quadsTree.quads_count()
        self.labelQuadsSelected.setText(f"{n}/{total} quads selected")

    def _check_has_items_checked(self):
        selected = self.mosaicsList.selected_mosaics()
        if selected:
            if self.btnOneOff.isChecked() and len(selected) > 1:
                self.parent.show_message(
                    'Only one single serie can be selected in "one off" mode.',
                    level=Qgis.Warning,
                    duration=10,
                )
                return False
            else:
                return True
        else:
            self.parent.show_message(
                "No checked items to order", level=Qgis.Warning, duration=10
            )
            return False

    def explore(self):
        if self._check_has_items_checked():
            selected = self.mosaicsList.selected_mosaics()

            analytics_track(BASEMAP_SERVICE_ADDED_TO_MAP)

            add_mosaics_to_qgis_project(
                selected, self.comboSeriesName.currentText() or selected[0][NAME]
            )

    def order(self):
        if self._check_has_items_checked():
            self.stackedWidget.setCurrentWidget(self.orderMethodPage)

    def next_order_method_page_clicked(self):
        if self.radioDownloadComplete.isChecked():
            mosaics = self.mosaicsList.selected_mosaics()
            quad = self.p_client.get_one_quad(mosaics[0])
            quadarea = self._area_from_bbox_coords(quad[BBOX])
            mosaicarea = self._area_from_bbox_coords(mosaics[0][BBOX])
            if mosaicarea > MAX_AREA_TO_DOWNLOAD:
                QMessageBox.warning(
                    self,
                    "Complete Download",
                    "This area is too big to download from the QGIS Plugin.<br>To"
                    " download a large Basemap area, you may want to consult our <a"
                    " href='https://developers.planet.com/docs/basemaps/'>developer"
                    " resources</a>",
                )
                return
            numquads = int(mosaicarea / quadarea)
            if numquads > MAX_QUADS_TO_DOWNLOAD:
                ret = QMessageBox.question(
                    self,
                    "Complete Download",
                    f"The download will contain more than {MAX_QUADS_TO_DOWNLOAD}"
                    " quads.\nAre your sure you want to proceed?",
                )
                if ret != QMessageBox.Yes:
                    return
            self.show_order_name_page()
        elif self.radioDownloadAOI.isChecked():
            self.labelWarningQuads.setText("")
            self.widgetProgressFindQuads.setVisible(False)
            self.stackedWidget.setCurrentWidget(self.orderAOIPage)
        elif self.radioStreaming.isChecked():
            self.show_order_streaming_page()

    def find_quads_clicked(self):
        self.labelWarningQuads.setText("")
        selected = self.mosaicsList.selected_mosaics()
        if not self.aoi_filter.leAOI.text():
            self.labelWarningQuads.setText("⚠️ No area of interest (AOI) defined")
            return
        geom = self.aoi_filter.aoi_as_4326_geom()
        if geom is None:
            self.parent.show_message(
                "Wrong AOI definition", level=Qgis.Warning, duration=10
            )
            return
        mosaic_extent = QgsRectangle(*selected[0][BBOX])
        if not geom.intersects(mosaic_extent):
            self.parent.show_message(
                "No mosaics in the selected area", level=Qgis.Warning, duration=10
            )
            return
        qgsarea = QgsDistanceArea()
        area = qgsarea.convertAreaMeasurement(
            qgsarea.measureArea(geom), QgsUnitTypes.AreaSquareKilometers
        )
        if area > MAX_AREA_TO_DOWNLOAD:
            QMessageBox.warning(
                self,
                "Quad Download",
                "This area is too big to download from the QGIS Plugin.<br>To download"
                " a large Basemap area, you may want to consult our <a"
                " href='https://developers.planet.com/docs/basemaps/'>developer"
                " resources</a>",
            )
            return
        self.find_quads()

    @waitcursor
    def find_quads(self):
        selected = self.mosaicsList.selected_mosaics()
        geom = self.aoi_filter.aoi_as_4326_geom()
        qgsarea = QgsDistanceArea()
        area = qgsarea.convertAreaMeasurement(
            qgsarea.measureArea(geom), QgsUnitTypes.AreaSquareKilometers
        )
        quad = self.p_client.get_one_quad(selected[0])
        quadarea = self._area_from_bbox_coords(quad[BBOX])
        numpages = math.ceil(area / quadarea / QUADS_PER_PAGE)

        self.widgetProgressFindQuads.setVisible(True)
        self.progressBarInstances.setMaximum(len(selected))
        self.progressBarQuads.setMaximum(numpages)
        self.finder = QuadFinder()
        self.finder.setup(self.p_client, selected, geom)

        self.objThread = QThread()
        self.finder.moveToThread(self.objThread)
        self.finder.finished.connect(self.objThread.quit)
        self.finder.finished.connect(self._update_quads)
        self.finder.mosaicStarted.connect(self._mosaic_started)
        self.finder.pageRead.connect(self._page_read)
        self.objThread.started.connect(self.finder.find_quads)
        self.objThread.start()

    def cancel_quad_search(self):
        self.finder.cancel()
        self.objThread.quit()
        self.widgetProgressFindQuads.setVisible(False)

    def _mosaic_started(self, i, name):
        self.labelProgressInstances.setText(
            f"Processing basemap '{name}' ({i}/{self.progressBarInstances.maximum()})"
        )
        self.progressBarInstances.setValue(i)
        QApplication.processEvents()

    def _page_read(self, i):
        total = self.progressBarQuads.maximum()
        self.labelProgressQuads.setText(
            f"Downloading quad footprints (page {i} of (estimated) {total})"
        )
        self.progressBarQuads.setValue(i)
        QApplication.processEvents()

    def _update_quads(self, quads):
        self._quads = quads
        self._populate_quads()

    def _populate_quads(self):
        selected = self.mosaicsList.selected_mosaics()
        if self.chkGroupByQuad.isChecked():
            self.quadsTree.populate_by_quad(selected, self._quads)
        else:
            self.quadsTree.populate_by_basemap(selected, self._quads)
        total_quads = self.quadsTree.quads_count()
        self.labelQuadsSummary.setText(
            f"{total_quads} quads from {len(selected)} basemap instances "
            "intersect your AOI for this basemap"
        )
        self.batch_select_quads_clicked("all")
        self.quads_selection_changed()
        self.widgetProgressFindQuads.setVisible(False)
        self.stackedWidget.setCurrentWidget(self.orderQuadsPage)

    def next_quads_page_clicked(self):
        selected = self.quadsTree.selected_quads()
        if len(selected) > MAX_QUADS_TO_DOWNLOAD:
            ret = QMessageBox.question(
                self,
                "Quad Download",
                f"The download will contain more than {MAX_QUADS_TO_DOWNLOAD} quads.\n"
                "Are your sure you want to proceed?",
            )
            if ret != QMessageBox.Yes:
                return
        if selected:
            self.show_order_name_page()
        else:
            self.parent.show_message(
                "No checked quads to order", level=Qgis.Warning, duration=10
            )

    def back_quads_page_clicked(self):
        self.quadsTree.clear()
        self.stackedWidget.setCurrentWidget(self.orderAOIPage)

    def show_order_streaming_page(self):
        selected = self.mosaicsList.selected_mosaics()
        name = selected[0][NAME]
        dates = date_interval_from_mosaics(selected)
        description = (
            f'<span style="color:black;"><b>{name}</b></span><br>'
            f'<span style="color:grey;">{len(selected)} instances | {dates}</span>'
        )
        self.labelStreamingOrderDescription.setText(description)
        pixmap = QPixmap(PLACEHOLDER_THUMB, "SVG")
        thumb = pixmap.scaled(
            48, 48, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self.labelStreamingOrderIcon.setPixmap(thumb)
        if THUMB in selected[0][LINKS]:
            self.set_summary_icon(selected[0][LINKS][THUMB])
        self.chkMinZoomLevel.setChecked(False)
        self.chkMaxZoomLevel.setChecked(False)
        self.comboMinZoomLevel.setEnabled(False)
        self.comboMaxZoomLevel.setEnabled(False)
        self.renderingOptions.set_datatype(selected[0][DATATYPE])
        self.stackedWidget.setCurrentWidget(self.orderStreamingPage)

    def _quads_summary(self):
        selected = self.mosaicsList.selected_mosaics()
        dates = date_interval_from_mosaics(selected)
        selected_quads = self.quadsTree.selected_quads()
        return f"{len(selected_quads)} quads | {dates}"

    def _quads_quota(self):
        selected_quads = self.quadsTree.selected_quads()
        total_area = 0
        for quad in selected_quads:
            total_area += self._area_from_bbox_coords(quad[BBOX])
        return total_area

    def _area_from_bbox_coords(self, bbox):
        qgsarea = QgsDistanceArea()
        extent = QgsRectangle(*bbox)
        geom = QgsGeometry.fromRect(extent)
        area = qgsarea.convertAreaMeasurement(
            qgsarea.measureArea(geom), QgsUnitTypes.AreaSquareKilometers
        )
        return area

    def show_order_name_page(self):
        QUAD_SIZE = 1
        selected = self.mosaicsList.selected_mosaics()
        if not self.btnOneOff.isChecked():
            name = self.comboSeriesName.currentText()
        else:
            name = selected[0][NAME]
        dates = date_interval_from_mosaics(selected)
        if self.radioDownloadComplete.isChecked():
            description = (
                f'<span style="color:black;"><b>{name}</b></span><br>'
                f'<span style="color:grey;">{len(selected)} instances | {dates}</span>'
            )

            title = "Order Complete Basemap"
            total_area = self._area_from_bbox_coords(selected[0][BBOX]) * len(selected)
            quad = self.p_client.get_one_quad(selected[0])
            quadarea = self._area_from_bbox_coords(quad[BBOX])
            numquads = total_area / quadarea
        elif self.radioDownloadAOI.isChecked():
            selected_quads = self.quadsTree.selected_quads()
            numquads = len(selected_quads)
            title = "Order Partial Basemap"
            description = (
                f'<span style="color:black;"><b>{name}</b></span><br>'
                f'<span style="color:grey;">{self._quads_summary()}</span>'
            )
            total_area = self._quads_quota()

        pixmap = QPixmap(PLACEHOLDER_THUMB, "SVG")
        thumb = pixmap.scaled(
            48, 48, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self.labelOrderIcon.setPixmap(thumb)
        if THUMB in selected[0][LINKS]:
            self.set_summary_icon(selected[0][LINKS][THUMB])
        self.labelOrderDescription.setText(description)
        self.grpBoxNamePage.setTitle(title)
        self.stackedWidget.setCurrentWidget(self.orderNamePage)
        self.txtOrderName.setText("")
        quota = self.p_client.user_quota_remaining()
        size = numquads * QUAD_SIZE
        if quota is not None:
            self.labelOrderInfo.setText(
                f"This Order will use {total_area:.2f} square km"
                f" of your remaining {quota} quota.\n\n"
                f"This Order's download size will be approximately {size} GB."
            )
            self.labelOrderInfo.setVisible(True)
        else:
            self.labelOrderInfo.setVisible(False)

    def set_summary_icon(self, iconurl):
        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self.iconDownloaded)
        self.nam.get(QNetworkRequest(QUrl(iconurl)))

    def iconDownloaded(self, reply):
        img = QImage()
        img.loadFromData(reply.readAll())
        pixmap = QPixmap(img)
        thumb = pixmap.scaled(
            48, 48, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        if self.radioStreaming.isChecked():
            self.labelStreamingOrderIcon.setPixmap(thumb)
        else:
            self.labelOrderIcon.setPixmap(thumb)

    def back_streaming_page_clicked(self):
        self.stackedWidget.setCurrentWidget(self.orderMethodPage)

    def back_name_page_clicked(self):
        if self.radioDownloadComplete.isChecked():
            self.stackedWidget.setCurrentWidget(self.orderMethodPage)
        elif self.radioDownloadAOI.isChecked():
            self.quadsTree.show_footprints()
            self.stackedWidget.setCurrentWidget(self.orderQuadsPage)

    def back_aoi_page_clicked(self):
        self.stackedWidget.setCurrentWidget(self.orderMethodPage)
        self.aoi_filter.reset_aoi_box()

    def submit_streaming_button_clicked(self):
        selected = self.mosaicsList.selected_mosaics()
        zmin = (
            self.comboMinZoomLevel.currentText()
            if self.chkMinZoomLevel.isChecked()
            else 0
        )
        zmax = (
            self.comboMaxZoomLevel.currentText()
            if self.chkMaxZoomLevel.isChecked()
            else 18
        )
        mosaicname = self.comboSeriesName.currentText() or selected[0][NAME]
        proc = self.renderingOptions.process()
        ramp = self.renderingOptions.ramp()

        analytics_track(BASEMAP_SERVICE_CONNECTION_ESTABLISHED)

        for mosaic in selected:
            name = f"{mosaicname} - {mosaic_title(mosaic)}"
            add_mosaics_to_qgis_project(
                [mosaic],
                name,
                proc=proc,
                ramp=ramp,
                zmin=zmin,
                zmax=zmax,
                add_xyz_server=True,
            )
        selected = self.mosaicsList.selected_mosaics()
        base_html = "<p>Your Connection(s) have been established</p>"
        self.grpBoxOrderConfirmation.setTitle("Order Streaming Download")
        dates = date_interval_from_mosaics(selected)
        description = f"{len(selected)} | {dates}"
        values = {"Series Name": mosaicname, "Series Instances": description}
        self.set_order_confirmation_summary(values, base_html)
        self.stackedWidget.setCurrentWidget(self.orderConfirmationPage)

    def submit_button_clicked(self):
        name = self.txtOrderName.text()
        if not bool(name.strip()):
            self.parent.show_message(
                "Enter a name for the order", level=Qgis.Warning, duration=10
            )
            return
        if self.radioDownloadComplete.isChecked():
            self.order_complete_submit()
        elif self.radioDownloadAOI.isChecked():
            self.order_partial_submit()

    def set_order_confirmation_summary(self, values, base_html=None):
        html = base_html or (
            "<p>Your order has been successfully submitted for processing.You may"
            " monitor its progress and availability in the <a href='#'>Order Status"
            " panel</a>.</p>"
        )
        html += "<p><table>"
        for k, v in values.items():
            html += f"<tr><td>{k}</td><td><b>{v}</b></td></tr>"
        html += "</table>"
        self.textBrowserOrderConfirmation.setHtml(html)

    @waitcursor
    def order_complete_submit(self):
        selected = self.mosaicsList.selected_mosaics()

        analytics_track(BASEMAP_COMPLETE_ORDER)

        name = self.txtOrderName.text()
        load_as_virtual = self.chkLoadAsVirtualLayer.isChecked()

        self.grpBoxOrderConfirmation.setTitle("Order Complete Download")
        dates = date_interval_from_mosaics(selected)
        description = f"{len(selected)} complete mosaics | {dates}"
        create_quad_order_from_mosaics(name, description, selected, load_as_virtual)
        refresh_orders()
        values = {
            "Order Name": self.txtOrderName.text(),
            "Series Name": self.comboSeriesName.currentText() or selected[0][NAME],
            "Series Instances": description,
        }
        self.set_order_confirmation_summary(values)
        self.stackedWidget.setCurrentWidget(self.orderConfirmationPage)

    def order_partial_submit(self):
        self.grpBoxOrderConfirmation.setTitle("Order Partial Download")
        mosaics = self.mosaicsList.selected_mosaics()
        quads_count = len(self.quadsTree.selected_quads())

        analytics_track(BASEMAP_PARTIAL_ORDER, {"count": quads_count})

        dates = date_interval_from_mosaics(mosaics)
        quads = self.quadsTree.selected_quads_classified()
        name = self.txtOrderName.text()
        load_as_virtual = self.chkLoadAsVirtualLayer.isChecked()
        description = f"{quads_count} quads | {dates}"
        create_quad_order_from_quads(name, description, quads, load_as_virtual)
        refresh_orders()
        values = {
            "Order Name": self.txtOrderName.text(),
            "Series Name": self.comboSeriesName.currentText() or mosaics[0][NAME],
            "Quads": self._quads_summary(),
            "Quota": self._quads_quota(),
        }
        self.set_order_confirmation_summary(values)
        self.quadsTree.clear()
        self.stackedWidget.setCurrentWidget(self.orderConfirmationPage)

    def close_aoi_page(self):
        self.aoi_filter.reset_aoi_box()
        self.quadsTree.clear()
        self.stackedWidget.setCurrentWidget(self.searchPage)


class QuadFinder(QObject):

    finished = pyqtSignal(list)
    pageRead = pyqtSignal(int)
    mosaicStarted = pyqtSignal(int, str)

    def setup(self, client, mosaics, geom):
        self.client = client
        self.mosaics = mosaics
        self.geom = geom

    def find_quads(self):
        self.canceled = False
        all_quads = []
        bbox_rect = self.geom.boundingBox()
        bbox = [
            bbox_rect.xMinimum(),
            bbox_rect.yMinimum(),
            bbox_rect.xMaximum(),
            bbox_rect.yMaximum(),
        ]
        for i, mosaic in enumerate(self.mosaics):
            self.mosaicStarted.emit(i + 1, mosaic.get(NAME))
            json_quads = []
            self.pageRead.emit(1)
            quads = self.client.get_quads_for_mosaic(mosaic, bbox)
            for j, page in enumerate(quads.iter()):
                json_quads.extend(page.get().get(MosaicQuads.ITEM_KEY))
                self.pageRead.emit(j + 2)
                if self.canceled:
                    return
            all_quads.append(json_quads)
        self.finished.emit(all_quads)

    def cancel(self):
        self.canceled = True
