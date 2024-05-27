# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ProgramacaoAplicadaGrupo2
                                 A QGIS plugin
 Solução do Grupo 2
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-04-28
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
__date__ = '2024-04-28'
__copyright__ = '(C) 2024 by Grupo 2'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterField,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingContext,
                       QgsProcessingParameterFeatureSink,
                       QgsFeedback,
                       QgsVectorLayer,
                       QgsProcessingException,
                       QgsField,
                       QgsFields,
                       QgsWkbTypes
                        )
from PyQt5.QtCore import QVariant
from qgis import processing


class ReambulacaoAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    PONTOS_GPS = "PONTOS_GPS"
    CAMADA_DIA_1 = "CAMADA_DIA_1"
    CAMPOS_IGNORADOS = "CAMPOS_IGNORADOS"
    CHAVE_PRIMARIA = "CHAVE_PRIMARIA"
    TOLERANCIA = "TOLERANCIA"
    CAMADA_DIA_2 = "CAMADA_DIA_2"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PONTOS_GPS,
                self.tr("Insira a camada com os pontos obtidos pelo GPS do operador"),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.CAMADA_DIA_1,
                self.tr("Insira a camada do dia 1"),
                types=[QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.CAMADA_DIA_2,
                self.tr("Insira a camada do dia 2"),
                types=[QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon]
            )
        )    

        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOLERANCIA, 
                self.tr("Insira a distância de tolerância entre o caminho percorrido e as mudanças (em graus)"),
                type=QgsProcessingParameterNumber.Double
                )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.CHAVE_PRIMARIA,
                self.tr("Escolha o atributo correspondente à chave primária"),
                parentLayerParameterName=self.CAMADA_DIA_1,
                type=QgsProcessingParameterField.Any
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPOS_IGNORADOS,
                self.tr("Escolha os atributos a serem IGNORADOS"),
                parentLayerParameterName=self.CAMADA_DIA_1,
                type=QgsProcessingParameterField.Any,
                allowMultiple=True,
                optional=True
            )
        )    

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).

        # Output layers

        ##tem que ter uma logica a depender da camada de entrada, se a camada dos dias for ponto, o output tem que ser ponto, e por aí vai, acho que isso vamos ajeitar no processamento, mas só colocando aqui para lembrar

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT, 
                self.tr("Output"))
        )    
    
    def processAlgorithm(self, parameters, context, feedback):
        # Retrieve parameters
        pontos_gps_camada = self.parameterAsVectorLayer(parameters, self.PONTOS_GPS, context)
        camada_dia_1 = self.parameterAsVectorLayer(parameters, self.CAMADA_DIA_1, context)
        camada_dia_2 = self.parameterAsVectorLayer(parameters, self.CAMADA_DIA_2, context)
        tol = self.parameterAsDouble(parameters, self.TOLERANCIA, context)
        chave_primaria = self.parameterAsString(parameters, self.CHAVE_PRIMARIA, context)
        campos_ignorados = self.parameterAsFields(parameters, self.CAMPOS_IGNORADOS, context)

        # Checar se as camadas do dia 1 e do dia 2 tem mesmo tipo de geometria
        if camada_dia_1.wkbType() != camada_dia_2.wkbType():
            raise QgsProcessingException(self.tr("As camadas do dia 1 e do dia 2 devem ter o mesmo tipo de geometria."))

        currentStep = 0
        multiStepFeedback = (
            QgsProcessingMultiStepFeedback(3, feedback)
            if feedback is not None
            else None
        )     
        if multiStepFeedback is not None:
            multiStepFeedback.setCurrentStep(currentStep)
            multiStepFeedback.pushInfo(
                self.tr("Gerando uma linha cujos vértices são os pontos da camada de pontos GPS, seguindo a ordem da data de criação...")
            )

        # Converter pontos GPS para uma linha
        linha_gps_camada = self.pointstopath(pontos_gps_camada, context, feedback)

        # Buffer em torno da linha percorrida (GPS)
        linha_gps_buffer = self.buffer(linha_gps_camada, tol, context, feedback)

        currentStep += 1
        if multiStepFeedback is not None:
            multiStepFeedback.setCurrentStep(currentStep)
            multiStepFeedback.pushInfo(
                self.tr("Próximo passo...")
            )

        fields = QgsFields()
        fields.append(QgsField(chave_primaria, QVariant.String))

        # Definir o tipo de geometria para o output
        geometry_type = camada_dia_1.wkbType()
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, geometry_type, camada_dia_1.sourceCrs())

        dict_dia_1 = {feat[chave_primaria]: feat for feat in camada_dia_1.getFeatures()}
        dict_dia_2 = {feat[chave_primaria]: feat for feat in camada_dia_2.getFeatures()}

        def add_feature_outside_tolerance(feat, tipo):
            new_feat = QgsFeature(fields)
            new_feat.setGeometry(feat.geometry())
            new_feat.setAttribute(chave_primaria, feat[chave_primaria])
            if self.is_outside_tolerance(feat.geometry(), linha_gps_buffer):
                sink.addFeature(new_feat, QgsFeatureSink.FastInsert)

        for key in dict_dia_1.keys() - dict_dia_2.keys():
            add_feature_outside_tolerance(dict_dia_1[key], "removida")

        for key in dict_dia_2.keys() - dict_dia_1.keys():
            add_feature_outside_tolerance(dict_dia_2[key], "adicionada")

        for key in dict_dia_1.keys() & dict_dia_2.keys():
            feat_dia_1 = dict_dia_1[key]
            feat_dia_2 = dict_dia_2[key]
            for field in feat_dia_1.fields().names():
                if field not in campos_ignorados:
                    if feat_dia_1[field] != feat_dia_2[field]:
                        add_feature_outside_tolerance(feat_dia_2, "modificada")
                        break

        return {self.OUTPUT: dest_id}

    def pointstopath(self, camada: QgsVectorLayer, context: QgsProcessingContext = None, feedback: QgsFeedback =None) -> QgsVectorLayer:
        output = processing.run(
            "native:pointstopath",
            {
                "INPUT": camada,
                "CLOSE_PATH": False,
                "ORDER_EXPRESSION":'"creation_time"',
                "NATURAL_SORT": False,
                "GROUP_EXPRESSION":'',
                "OUTPUT": "memory:"
            },
            context=context,
            feedback = feedback
        )["OUTPUT"]
        return output
    
    def buffer(self, camada:QgsVectorLayer, valor: float, context: QgsProcessingContext = None, feedback: QgsFeedback =None) -> QgsVectorLayer:
        output = processing.run(
            "native:buffer",
            {
                "INPUT": camada,
                "DISTANCE": valor,
                "OUTPUT": "memory:"
            },
            context=context,
            feedback = feedback
        )["OUTPUT"]
        return output   

    def is_outside_tolerance(self, geom, buffer_layer):
        """Check if the geometry is outside the tolerance (buffer)."""
        for feature in buffer_layer.getFeatures():
            buffer_geom = feature.geometry()
            if geom.within(buffer_geom):
                return False
        return True  


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Solução do projeto 3'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Projeto 3'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ReambulacaoAlgorithm()
