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


class ValidacaoAlgorithm(QgsProcessingAlgorithm):
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

    ELEMENTO_VIARIO = "ELEMENTO_VIARIO"
    TRECHO_DRENAGEM = "TRECHO_DRENAGEM"
    VIA_DESLOC = "VIA_DESLOC"
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
                self.ELEMENTO_VIARIO,
                self.tr("Insira a camada de elemento viário (ponto)"),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.TRECHO_DRENAGEM,
                self.tr("Insira a camada de trecho de drenagem"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.VIA_DESLOC,
                self.tr("Insira a camada de via de deslocamento"),
                types=[QgsProcessing.TypeVectorLine]
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
        elemento_viario_camada = self.parameterAsVectorLayer(parameters, self.ELEMENTO_VIARIO, context)
        trecho_drenagem_camada = self.parameterAsVectorLayer(parameters, self.TRECHO_DRENAGEM, context)
        via_deslocamento_camada = self.parameterAsVectorLayer(parameters, self.VIA_DESLOC, context)

        currentStep = 0
        multiStepFeedback = (
            QgsProcessingMultiStepFeedback(3, feedback)
            if feedback is not None
            else None
        )     
        if multiStepFeedback is not None:
            multiStepFeedback.setCurrentStep(currentStep)
            multiStepFeedback.pushInfo(
                self.tr("Primeiro passo")
            )

        currentStep += 1
        if multiStepFeedback is not None:
            multiStepFeedback.setCurrentStep(currentStep)
            multiStepFeedback.pushInfo(
                self.tr("Próximo passo...")
            )

        # Definir o tipo de geometria para o output
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context)

        return {self.OUTPUT: dest_id}

    #aqui estão os processings que foram utilizados

    #aqui começam funções que caracterizam o plugin

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Solução do projeto 4'

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
        return 'Projeto 4'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ValidacaoAlgorithm()