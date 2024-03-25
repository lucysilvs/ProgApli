# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ProgramacaoAplicadaGrupo2
                                 A QGIS plugin
 Solução do Grupo 2
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-03-24
        copyright            : (C) 2024 by Grupo 2
        email                : analivia.200012@ime.eb.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Grupo 2'
__date__ = '2024-03-24'
__copyright__ = '(C) 2024 by Grupo 2'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


# -- coding: utf-8 --

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterDistance,
                       QgsProcessingUtils)
from qgis import processing

import numpy

class TrafegabilidadeAlgorithm(QgsProcessingAlgorithm):
    INPUT_VIAS = 'INPUT_VIAS'
    BUFFER_VIAS = 'BUFFER_VIAS'
    INPUT_VEGETACAO = 'INPUT_VEGETACAO'
    INPUT_MASSA_DAGUA = 'INPUT_MASSA_DAGUA'
    INPUT_TRECHO_DRENAGEM = 'INPUT_TRECHO_DRENAGEM'
    BUFFER_DRENAGEM = 'BUFFER_DRENAGEM'
    INPUT_AREA_EDIFICADA = 'INPUT_AREA_EDIFICADA'
    PIXEL_SIZE = 'PIXEL_SIZE'
    OUTPUT_RASTER = 'OUTPUT_RASTER'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TrafegabilidadeAlgorithm()

    def name(self):
        return 'trafegabilidade'

    def displayName(self):
        return self.tr('Carta de Trafegabilidade')

    def group(self):
        return self.tr('Exemplos')

    def groupId(self):
        return 'exemplos'

    def shortHelpString(self):
        return self.tr("Cria um raster de trafegabilidade com base em critérios específicos.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_VIAS, self.tr('Vias de Deslocamento')))
        self.addParameter(QgsProcessingParameterDistance(self.BUFFER_VIAS, self.tr('Buffer para Vias de Deslocamento'), parentParameterName=self.INPUT_VIAS))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_VEGETACAO, self.tr('Vegetação')))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_MASSA_DAGUA, self.tr('Massa d\'Água')))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_TRECHO_DRENAGEM, self.tr('Trecho de Drenagem')))
        self.addParameter(QgsProcessingParameterDistance(self.BUFFER_DRENAGEM, self.tr('Buffer para Trecho de Drenagem'), parentParameterName=self.INPUT_TRECHO_DRENAGEM))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_AREA_EDIFICADA, self.tr('Área Edificada')))
        self.addParameter(QgsProcessingParameterNumber(self.PIXEL_SIZE, self.tr('Tamanho do Pixel'), QgsProcessingParameterNumber.Double, 10.0))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_RASTER, self.tr('Raster de Trafegabilidade')))

    def processAlgorithm(self, parameters, context, feedback):
        vias = self.parameterAsVectorLayer(parameters, self.INPUT_VIAS, context)
        buffer_vias = self.parameterAsDouble(parameters, self.BUFFER_VIAS, context)
        vegetacao = self.parameterAsVectorLayer(parameters, self.INPUT_VEGETACAO, context)
        massa_dagua = self.parameterAsVectorLayer(parameters, self.INPUT_MASSA_DAGUA, context)
        trecho_drenagem = self.parameterAsVectorLayer(parameters, self.INPUT_TRECHO_DRENAGEM, context)
        buffer_drenagem = self.parameterAsDouble(parameters, self.BUFFER_DRENAGEM, context)
        area_edificada = self.parameterAsVectorLayer(parameters, self.INPUT_AREA_EDIFICADA, context)
        pixel_size = self.parameterAsDouble(parameters, self.PIXEL_SIZE, context)
        output_raster_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

        # Criação do raster base
        extent = vias.extent()
        extent.combineExtentWith(vegetacao.extent())
        extent.combineExtentWith(massa_dagua.extent())
        extent.combineExtentWith(trecho_drenagem.extent())
        extent.combineExtentWith(area_edificada.extent())
        crs = vias.crs()
        cols = int((extent.xMaximum() - extent.xMinimum()) / pixel_size)
        rows = int((extent.yMaximum() - extent.yMinimum()) / pixel_size)

        # Criar uma matriz de zeros para armazenar os valores de raster
        raster_data = numpy.zeros((rows, cols), dtype=numpy.float32)

        # Rasterize as camadas vetoriais com os valores correspondentes
        # Adequado (1) para vias de deslocamento (buffer)
        temp_buffer_vias_path = QgsProcessingUtils.generateTempFilename('buffer_vias.shp')
        processing.run("native:buffer", {
            'INPUT': vias,
            'DISTANCE': buffer_vias,
            'SEGMENTS': 5,
            'END_CAP_STYLE': 0,
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'DISSOLVE': False,
            'OUTPUT': temp_buffer_vias_path
        }, context=context, feedback=feedback)

        processing.run("gdal:rasterize", {
            'INPUT': temp_buffer_vias_path,
            'FIELD': None,
            'BURN': 1,
            'UNITS': 1,
            'WIDTH': pixel_size,
            'HEIGHT': pixel_size,
            'EXTENT': extent,
            'NODATA': 0,
            'OPTIONS': '',
            'DATA_TYPE': 5,
            'INIT': None,
            'INVERT': False,
            'OUTPUT': output_raster_path
        }, context=context, feedback=feedback)

        # Impeditivo (3) para vegetação, massa d'água, trecho de drenagem (buffer)
        for layer in [vegetacao, massa_dagua, trecho_drenagem]:
            temp_layer_path = QgsProcessingUtils.generateTempFilename('buffer_layer.shp')
            processing.run("native:buffer", {
                'INPUT': layer,
                'DISTANCE': buffer_drenagem,
                'SEGMENTS': 5,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'DISSOLVE': False,
                'OUTPUT': temp_layer_path
            }, context=context, feedback=feedback)

            processing.run("gdal:rasterize", {
                'INPUT': temp_layer_path,
                'FIELD': None,
                'BURN': 3,
                'UNITS': 1,
                'WIDTH': pixel_size,
                'HEIGHT': pixel_size,
                'EXTENT': extent,
                'NODATA': 0,
                'OPTIONS': '',
                'DATA_TYPE': 5,
                'INIT': None,
                'INVERT': False,
                'OUTPUT': output_raster_path
            }, context=context, feedback=feedback)

        # Restritivo (2) para área edificada
        temp_area_edificada_path = QgsProcessingUtils.generateTempFilename('area_edificada.shp')
        processing.run("native:buffer", {
            'INPUT': area_edificada,
            'DISTANCE': buffer_drenagem,
            'SEGMENTS': 5,
            'END_CAP_STYLE': 0,
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'DISSOLVE': False,
            'OUTPUT': temp_area_edificada_path
        }, context=context, feedback=feedback)

        processing.run("gdal:rasterize", {
            'INPUT': temp_area_edificada_path,
            'FIELD': None,
            'BURN': 2,
            'UNITS': 1,
            'WIDTH': pixel_size,
            'HEIGHT': pixel_size,
            'EXTENT': extent,
            'NODATA': 0,
            'OPTIONS': '',
            'DATA_TYPE': 5,
            'INIT': None,
            'INVERT': False,
            'OUTPUT': output_raster_path
        }, context=context, feedback=feedback)

        return {self.OUTPUT_RASTER: output_raster_path}
