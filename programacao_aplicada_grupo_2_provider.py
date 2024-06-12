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

from qgis.core import QgsProcessingProvider
from .algorithms.Projeto1.solucao import TrafegabilidadeAlgorithm
from .algorithms.Projeto2.solucao import DadosMDTAlgorithm
from .algorithms.Projeto2.solucao_complementar import DadosMDTComplementarAlgorithm
from .algorithms.Projeto3.solucao import ReambulacaoAlgorithm
from .algorithms.Projeto3.solucao_complementar import ReambulacaoComplementarAlgorithm
from .algorithms.Projeto4.solucao import ValidacaoAlgorithm
from .algorithms.Projeto4.solucao_complementar import ValidacaoComplementarAlgorithm


class ProgramacaoAplicadaGrupo2Provider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(TrafegabilidadeAlgorithm())
        self.addAlgorithm(DadosMDTAlgorithm())
        self.addAlgorithm(DadosMDTComplementarAlgorithm())
        self.addAlgorithm(ReambulacaoAlgorithm())
        self.addAlgorithm(ReambulacaoComplementarAlgorithm())
        self.addAlgorithm(ValidacaoAlgorithm())
        self.addAlgorithm(ValidacaoComplementarAlgorithm())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'ProgramacaoAplicadaGrupo2'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('ProgramacaoAplicadaGrupo2')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
