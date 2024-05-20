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
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterRasterLayer,
                       QgsVectorLayer,
                       QgsProcessingException,
                       QgsFeatureRequest,
                       QgsProject,
                       QgsFeature,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingContext,
                       QgsFeedback
                        )
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
                self.EDIFICACAO_PONTO_DIA_1,
                self.tr("Insira a camada do dia 1"),
                types=[QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.EDIFICACAO_PONTO_DIA_1,
                self.tr("Insira a camada do dia 2"),
                types=[QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon]
            )
        )        

##adicionei esse modelo para ser o input da tolreancia, mas tem que mexer ainda, não sei se vai ser buffer mesmo ou se vamos ter que usar outra forma de distancia
        self.addParameter(
            QgsProcessingParameterDistance(
                self.BUFFER_VIA_DESLOCAMENTO,
                self.tr("Insira o valor do buffer para via de deslocamento"),
                parentParameterName=self.VIA_DESLOCAMENTO
            )
        )

##aqui ainda falta adicionar dois inputs: o do atributo correspondente à chave primaria e o dos atributos a serem ignorados (não sei como faz input de atributo)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).

        # Output layers

        ##teremos apenas um output, tem que ajeitar aqui ainda
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr("output do projeto 3 *mudar*")
            )
        )      
    
    
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        pontos_gps_camada = self.parameterAsVectorLayer(parameters, self.PONTOS_GPS, context)
        camada_dia_1 = self.parameterAsVectorLayer(parameters, self.CAMADA_DIA_1, context)
        camada_dia_2 = self.parameterAsVectorLayer(parameters, self.CAMADA_DIA_2, context)
        output = self.parameterAsString(parameters, self.OUTPUT, context)

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

        linha_gps_camada = self.pointstopath(pontos_gps_camada, context)
        
        # Adicionar camada resultante ao projeto do QGIS
        QgsProject.instance().addMapLayer(linha_gps_camada)

        currentStep += 1
        if multiStepFeedback is not None:
            multiStepFeedback.setCurrentStep(currentStep)
            multiStepFeedback.pushInfo(
                self.tr("Proximo passo...")
            )

        # Retornar o resultado do algoritmo
        return {self.OUTPUT: output}
    

    ##Essa parte é para colocarmos os processings utilizados na solução
    
    #processing.run("native:pointstopath", {'INPUT':'C:/Users/anali/OneDrive/Documentos/prog_apli_docs/proj3/dados_projeto3_2024.gpkg|layername=tracker','CLOSE_PATH':False,'ORDER_EXPRESSION':'"creation_time"','NATURAL_SORT':False,'GROUP_EXPRESSION':'','OUTPUT':'TEMPORARY_OUTPUT'})
    
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
