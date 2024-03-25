# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination,
                       QgsRasterFileWriter,
                       QgsRasterLayer,
                       QgsRectangle,
                       QgsPointXY,
                       QgsWkbTypes,
                       Qgis,
                       QgsProcessingParameterDistance)
from qgis import processing

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

        raster_writer = QgsRasterFileWriter(output_raster_path)
        data_provider = raster_writer.createOneBandRaster(Qgis.Float32, cols, rows, extent, crs)
        if not data_provider:
            raise QgsProcessingException("Erro ao criar o raster base.")

        # Preencha o raster com o valor inicial 'Desconhecido' (0)
        for row in range(rows):
            block = data_provider.block(0, extent, cols, 1)
            for col in range(cols):
                block.setValue(col, 0, 0)
            data_provider.writeBlock(block, row)

        # Cria buffers para vias de deslocamento e trecho de drenagem
        buffer_vias_layer = processing.run("native:buffer", {
            'INPUT': vias,
            'DISTANCE': buffer_vias,
            'SEGMENTS': 5,
            'END_CAP_STYLE': 0,
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'DISSOLVE': False,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)['OUTPUT']

        buffer_drenagem_layer = processing.run("native:buffer", {
            'INPUT': trecho_drenagem,
            'DISTANCE': buffer_drenagem,
            'SEGMENTS': 5,
            'END_CAP_STYLE': 0,
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'DISSOLVE': False,
            'OUTPUT': 'memory:'
        }, context=context, feedback=feedback)['OUTPUT']

        # Adiciona informações ao raster com base nas camadas de entrada
        for layer, value in [(buffer_vias_layer, 1), (vegetacao, 3), (massa_dagua, 3), (buffer_drenagem_layer, 3), (area_edificada, 2)]:
            for feat in layer.getFeatures():
                geom = feat.geometry()
                bbox = geom.boundingBox()
                min_x = bbox.xMinimum()
                max_x = bbox.xMaximum()
                min_y = bbox.yMinimum()
                max_y = bbox.yMaximum()
                for y in range(rows):
                    for x in range(cols):
                        # Calcula a posição do centro do pixel
                        pixel_x = extent.xMinimum() + x * pixel_size + pixel_size / 2
                        pixel_y = extent.yMinimum() + y * pixel_size + pixel_size / 2
                        if min_x <= pixel_x <= max_x and min_y <= pixel_y <= max_y:
                            block = data_provider.block(0, QgsRectangle(pixel_x - pixel_size / 2, pixel_y - pixel_size / 2, pixel_x + pixel_size / 2, pixel_y + pixel_size / 2), 1, 1)
                            block.setValue(0, 0, value)
                            data_provider.writeBlock(block, y)

        raster_writer.finish()



