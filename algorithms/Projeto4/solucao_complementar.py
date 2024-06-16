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

class ValidacaoComplementarAlgorithm(QgsProcessingAlgorithm):
    ELEMENTO_VIARIO = "ELEMENTO_VIARIO"
    TRECHO_DRENAGEM = "TRECHO_DRENAGEM"
    VIA_DESLOC = "VIA_DESLOC"
    MASSA_AGUA = "MASSA_AGUA"
    BARRAGEM = "BARRAGEM"
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
            QgsProcessingParameterVectorLayer(
                self.MASSA_AGUA,
                self.tr("Insira a camada de massa d'água"),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.BARRAGEM,
                self.tr("Insira a camada de barragem"),
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
        massa_agua_camada = self.parameterAsVectorLayer(parameters, self.MASSA_AGUA, context)
        barragem_camada = self.parameterAsVectorLayer(parameters, self.BARRAGEM, context)

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

                #Regra 1.1
                if 'situacao_fisica' in feature.fields().names() and feature['situacao_fisica'] != 3:
                    new_feature['erro'] = "erro na regra 1 - não possui o atributo 'situacao_fisica' preenchido com 3 (Construída)"
                    sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

                #Regra 1.2
                if 'tipo' in feature.fields().names() and feature['tipo'] == 401 and feature['material_construcao'] != 97:
                    new_feature['erro'] = "erro na regra 1 - 'material_construcao' não é 97 (não aplicável) para 'tipo' 401"
                    sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

                #Regra 1.3
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

        vertices_trecho_drenagem = self.extractvertices(trecho_drenagem_camada, context, feedback)
        vertices_via_deslocamento = self.extractvertices(via_deslocamento_camada, context, feedback)
        intersecoes_camada = self.lineintersections(trecho_drenagem_camada, via_deslocamento_camada, context, feedback)
        intersecao1 = self.intersection(intersecoes_camada, vertices_trecho_drenagem, context, feedback)
        intersecao2 = self.intersection(intersecao1, vertices_via_deslocamento, context, feedback)

        intersecao2_ids = {f['id'] for f in intersecao2.getFeatures()}
        for feature in intersecoes_camada.getFeatures():
            if feature['id'] not in intersecao2_ids:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']
                new_feature['erro'] = "erro na regra 2"
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        #Regra 3
        filtered_layer = self.filtrar_tipos(elemento_viario_camada, context, feedback)
        intersecao3 = self.intersection(intersecoes_camada, filtered_layer, context, feedback)

        intersecao3_ids = {f['id'] for f in intersecao3.getFeatures()}
        ids_ja_adicionados = set()
        for feature in intersecoes_camada.getFeatures():
            if feature['id'] not in intersecao3_ids and feature['id'] not in ids_ja_adicionados:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']
                new_feature['erro'] = "erro na regra 3"
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
                ids_ja_adicionados.add(feature['id'])

        #Regra 4
        filtered_layer2 = self.filtrar_tipos2(elemento_viario_camada, context, feedback)
        intersecao4 = self.intersection(filtered_layer2, intersecoes_camada, context, feedback)

        intersecao4_ids = {f['id'] for f in intersecao4.getFeatures()}
        for feature in filtered_layer2.getFeatures():
            if feature['id'] not in intersecao4_ids:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']
                new_feature['erro'] = "erro na regra 4"
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        # Regra 5
        filtered_layer3 = self.filtrar_tipos3(elemento_viario_camada, context, feedback)
        ponte_ids = set()
        for ponte in filtered_layer3.getFeatures():
            ponte_geom = ponte.geometry().asPoint()
            coincidentes = [via for via in vertices_via_deslocamento.getFeatures() if via.geometry().asPoint().distance(ponte_geom) < 1e-6]

            if coincidentes:
                for via in coincidentes:
                    if (ponte['nr_faixas'] != via['nr_faixas'] or
                        ponte['nr_pistas'] != via['nr_pistas'] or
                        ponte['situacao_fisica'] != via['situacao_fisica']):
                        if ponte['id'] not in ponte_ids:
                            new_feature = QgsFeature(campos)
                            new_feature.setGeometry(ponte.geometry())
                            new_feature['id'] = ponte['id']
                            new_feature['erro'] = "erro na regra 5 - atributos da ponte não coincidem com a via"
                            ponte_ids.add(new_feature['id'])
                            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
            else:
                if ponte['id'] not in ponte_ids:
                    new_feature = QgsFeature(campos)
                    new_feature.setGeometry(ponte.geometry())
                    new_feature['id'] = ponte['id']
                    new_feature['erro'] = "erro na regra 5 - ponte não coincide com um vértice de via de deslocamento"
                    ponte_ids.add(new_feature['id'])
                    sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        #Regra 6
        filtered_layer4 = self.filtrar_tipos4(massa_agua_camada, context, feedback)
        massa_agua_limite = self.boundary(filtered_layer4, context, feedback)
        intersecao5 = self.intersection(massa_agua_limite, barragem_camada, context, feedback)
        massa_agua_limite_p = self.pointonsurface(massa_agua_limite, context, feedback)
        intersecao5_p = self.pointonsurface(intersecao5, context, feedback)


        intersecao5_p_ids = {f['id'] for f in intersecao5_p.getFeatures()}
        for feature in massa_agua_limite_p.getFeatures():
            if feature['id'] not in intersecao5_p_ids:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']
                new_feature['erro'] = "erro na regra 6 - Borda da massa d'água não coincide com uma barragem"
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        #Regra 7
        filtered_layer5 = self.filtrar_tipos5(via_deslocamento_camada, context, feedback)
        intersecao6 = self.intersection(barragem_camada, filtered_layer5, context, feedback)
        intersecao6_p = self.pointonsurface(intersecao6, context, feedback)
        barragem_camada_p = self.pointonsurface(barragem_camada, context, feedback)

        intersecao6_ids = {f['id'] for f in intersecao6_p.getFeatures()}
        filtered_layer5_ids = {f['id'] for f in filtered_layer5.getFeatures()}

        #Pontos na interseção que não estão preenchidos com "Sim (1)"
        for feature in barragem_camada_p.getFeatures():
            if feature['id'] in intersecao6_ids and feature['sobreposto_transportes'] != 1:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']
                new_feature['erro'] = "erro na regra 7 - está sobreposto à uma vida de deslocamento, porém não possui 'sobreposto_transportes' preenchido com 'Sim'"
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        #Pontos na barragem_camada_p que não estão na intersecao6_p e não preenchidos com "Não (2)"
        for feature in barragem_camada_p.getFeatures():
            if (feature['id'] not in intersecao6_ids and feature['id'] in filtered_layer5_ids) and feature['sobreposto_transportes'] != 2:
                new_feature = QgsFeature(campos)
                new_feature.setGeometry(feature.geometry())
                new_feature['id'] = feature['id']
                new_feature['erro'] = "erro na regra 7 - não está sobreposto à uma vida de deslocamento, porém não possui 'sobreposto_transportes' preenchido com 'Não'"
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

    def filtrar_tipos4(self, camada, context, feedback):
        expression = '"tipo" IN (10,11)'
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
    
    
    def filtrar_tipos5(self, camada, context, feedback):
        expression = '"tipo" IN (2)'
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

    def boundary(self, camada, context, feedback):
        output = processing.run(
            "native:boundary",
            {
                "INPUT": camada,
                "OUTPUT": "memory:"
            },
            context=context,
            feedback=feedback
        )["OUTPUT"]
        return output

    def name(self):
        return 'Solução complementar do projeto 4'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return 'Projeto 4'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ValidacaoComplementarAlgorithm()

