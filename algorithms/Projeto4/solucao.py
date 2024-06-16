from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingMultiStepFeedback,
                       QgsFeatureSink,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       NULL)
from qgis import processing

class ValidacaoAlgorithm(QgsProcessingAlgorithm):
    ELEMENTO_VIARIO = "ELEMENTO_VIARIO"
    TRECHO_DRENAGEM = "TRECHO_DRENAGEM"
    VIA_DESLOC = "VIA_DESLOC"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config=None):
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

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Output"))
        )

    def processAlgorithm(self, parameters, context, feedback):
        elemento_viario_camada = self.parameterAsVectorLayer(parameters, self.ELEMENTO_VIARIO, context)
        trecho_drenagem_camada = self.parameterAsVectorLayer(parameters, self.TRECHO_DRENAGEM, context)
        via_deslocamento_camada = self.parameterAsVectorLayer(parameters, self.VIA_DESLOC, context)

        multiStepFeedback = QgsProcessingMultiStepFeedback(3, feedback) if feedback is not None else None

        ponto_camadas = [elemento_viario_camada,
                         self.pointonsurface(trecho_drenagem_camada, context, feedback),
                         self.pointonsurface(via_deslocamento_camada, context, feedback)]

        campos = QgsFields()
        campos.append(QgsField('erro', QVariant.String))
        campos.append(QgsField('id', QVariant.String))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, campos, elemento_viario_camada.wkbType(), elemento_viario_camada.sourceCrs())

        for camada in ponto_camadas:
            for feature in camada.getFeatures():
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']

                # Rule 1.1: situacao_fisica must be 3 (Construída)
                if 'situacao_fisica' in feature.fields().names() and feature['situacao_fisica'] != 3:
                    new_feature['erro'] = "erro na regra 1 - não possui o atributo 'situacao_fisica' preenchido com 3 (Construída)"
                    sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

                # Rule 1.2: tipo 401 and material_construcao not equal to 97
                if 'tipo' in feature.fields().names() and feature['tipo'] == 401 and feature['material_construcao'] != 97:
                    new_feature['erro'] = "erro na regra 1 - 'material_construcao' não é 97 (não aplicável) para 'tipo' 401"
                    sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

                # Rule 1.3: via de deslocamento or tipo 203 must have nr_pistas <= nr_faixas and both at least 1
                if camada == ponto_camadas[2] or ('tipo' in feature.fields().names() and feature['tipo'] == 203):
                    if 'nr_pistas' in feature.fields().names() and 'nr_faixas' in feature.fields().names():
                        nr_pistas = feature['nr_pistas']
                        nr_faixas = feature['nr_faixas']

                        # Check if nr_pistas and nr_faixas are NULL
                        if nr_pistas == NULL or nr_faixas == NULL:
                            new_feature['erro'] = "erro na regra 1 - 'nr_pistas' e 'nr_faixas' devem ser no mínimo 1"
                            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
                        else:
                            nr_pistas = int(nr_pistas)
                            nr_faixas = int(nr_faixas)
                            if nr_pistas < 1 or nr_faixas < 1:
                                new_feature['erro'] = "erro na regra 1 - 'nr_pistas' e 'nr_faixas' devem ser no mínimo 1"
                                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
                            elif nr_pistas > nr_faixas:
                                new_feature['erro'] = "erro na regra 1 - 'nr_pistas' não pode ser maior que 'nr_faixas'"
                                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        # Extract vertices and find intersections
        vertices_trecho_drenagem = self.extractvertices(trecho_drenagem_camada, context, feedback)
        vertices_via_deslocamento = self.extractvertices(via_deslocamento_camada, context, feedback)
        intersecoes_camada = self.lineintersections(trecho_drenagem_camada, via_deslocamento_camada, context, feedback)
        intersecao1 = self.intersection(intersecoes_camada, vertices_trecho_drenagem, context, feedback)
        intersecao2 = self.intersection(intersecao1, vertices_via_deslocamento, context, feedback)

        # Identify IDs in intersecoes_camada not in intersecao2
        intersecao2_ids = {f['id'] for f in intersecao2.getFeatures()}
        for feature in intersecoes_camada.getFeatures():
            if feature['id'] not in intersecao2_ids:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']
                new_feature['erro'] = "erro na regra 2"
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        # Regra 3: Interseção com tipos específicos
        filtered_layer = self.filtrar_tipos(elemento_viario_camada, context, feedback)
        intersecao3 = self.intersection(intersecoes_camada, filtered_layer, context, feedback)

        # Identify IDs in intersecoes_camada not in intersecao3
        intersecao3_ids = {f['id'] for f in intersecao3.getFeatures()}
        for feature in intersecoes_camada.getFeatures():
            if feature['id'] not in intersecao3_ids:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']
                new_feature['erro'] = "erro na regra 3"
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        # Regra 4: Interseção com tipos e modal_uso específicos
        filtered_layer2 = self.filtrar_tipos2(elemento_viario_camada, context, feedback)
        intersecao4 = self.intersection(filtered_layer2, intersecoes_camada, context, feedback)

        # Identify IDs in intersecao4 not in intersecoes_camada
        intersecao4_ids = {f['id'] for f in intersecao4.getFeatures()}
        for feature in filtered_layer2.getFeatures():
            if feature['id'] not in intersecao4_ids:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']
                new_feature['erro'] = "erro na regra 4"
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        # Regra 5: Garantir que as pontes coincidam com vértices de via de deslocamento e atributos coincidam
        filtered_layer3 = self.filtrar_tipos3(elemento_viario_camada, context, feedback)
        for ponte in filtered_layer3.getFeatures():
            ponte_geom = ponte.geometry().asPoint()
            coincidentes = [via for via in vertices_via_deslocamento.getFeatures() if via.geometry().asPoint().distance(ponte_geom) < 1e-6]

            if coincidentes:
                for via in coincidentes:
                    if (ponte['nr_faixas'] != via['nr_faixas'] or
                        ponte['nr_pistas'] != via['nr_pistas'] or
                        ponte['situacao_fisica'] != via['situacao_fisica']):
                        new_feature = QgsFeature(campos)
                        new_feature.setGeometry(ponte.geometry())
                        new_feature['id'] = ponte['id']
                        new_feature['erro'] = "erro na regra 5 - atributos da ponte não coincidem com a via"
                        sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
            else:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(ponte.geometry())
                new_feature['id'] = ponte['id']
                new_feature['erro'] = "erro na regra 5 - ponte não coincide com um vértice de via de deslocamento"
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}

    def pointonsurface(self, camada, context, feedback):
        output = processing.run(
            "native:pointonsurface",
            {
                "INPUT": camada,
                "ALL_PARTS": False,
                "OUTPUT": "memory:"
            },
            context=context,
            feedback=feedback
        )["OUTPUT"]
        return output

    def extractvertices(self, camada, context, feedback):
        output = processing.run(
            "native:extractvertices",
            {
                "INPUT": camada,
                "OUTPUT": "memory:"
            },
            context=context,
            feedback=feedback
        )["OUTPUT"]
        return output

    def lineintersections(self, camada1, camada2, context, feedback):
        output = processing.run(
            "native:lineintersections",
            {
                "INPUT": camada1,
                "INTERSECT": camada2,
                "INPUT_FIELDS": [],
                "INTERSECT_FIELDS": [],
                "INTERSECT_FIELDS_PREFIX": '',
                "OUTPUT": "memory:"
            },
            context=context,
            feedback=feedback
        )["OUTPUT"]
        return output

    def intersection(self, camada1, camada2, context, feedback):
        output = processing.run(
            "native:intersection",
            {
                "INPUT": camada1,
                "OVERLAY": camada2,
                "INPUT_FIELDS": [],
                "OVERLAY_FIELDS": [],
                "OVERLAY_FIELDS_PREFIX": '',
                "GRID_SIZE": None,
                "OUTPUT": "memory:"
            },
            context=context,
            feedback=feedback
        )["OUTPUT"]
        return output

    def filtrar_tipos(self, camada, context, feedback):
        expression = '"tipo" IN (501, 401, 203)'
        filtered_layer = processing.run(
            "native:extractbyexpression",
            {
                'INPUT': camada,
                'EXPRESSION': expression,
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback
        )["OUTPUT"]
        return filtered_layer

    def filtrar_tipos2(self, camada, context, feedback):
        expression = '"tipo" IN (501, 401, 203) AND "modal_uso" = 4'
        filtered_layer = processing.run(
            "native:extractbyexpression",
            {
                'INPUT': camada,
                'EXPRESSION': expression,
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback
        )["OUTPUT"]
        return filtered_layer

    def filtrar_tipos3(self, camada, context, feedback):
        expression = '"tipo" IN (203) AND "modal_uso" = 4'
        filtered_layer = processing.run(
            "native:extractbyexpression",
            {
                'INPUT': camada,
                'EXPRESSION': expression,
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback
        )["OUTPUT"]
        return filtered_layer

    def name(self):
        return 'Solução do projeto 4'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return 'Projeto 4'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ValidacaoAlgorithm()
