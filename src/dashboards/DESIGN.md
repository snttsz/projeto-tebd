# Direção visual — Ciclo Urbano em React

## Intenção

Uma central de acompanhamento da coleta, pronta para a demonstração acadêmica: o panorama abre com a evolução mensal e a composição dos resíduos; os três níveis mantêm todas as perguntas e seus resultados verificáveis. A interface utiliza os dados preservados, sem inventar séries, metas cumpridas ou geometrias de mapa.

## Sistema

- Azul profundo `#192f58`: títulos e navegação.
- Índigo `#5865df`: série principal e seleção.
- Verde `#15967d`: recicláveis e ações ambientais.
- Âmbar `#c58126`: atenção e ressalvas.
- Cinza azulado `#f3f5fb`: fundo da aplicação.
- Branco `#ffffff`: superfícies de leitura.
- Tipografia: Manrope local, pesos 400–800; medidas com algarismos tabulares.
- Layout: barra lateral fixa no desktop, navegação compacta no celular, conteúdo alinhado à esquerda e gráficos de tamanhos proporcionais à sua importância.

```text
marca / navegação | contexto e ações
                 | título e indicadores do período
                 | evolução mensal (ampla) | composição
                 | perfil dos bairros     | prioridades
```

## Revisão antes de construir

Uma grade de cartões iguais esconderia a diferença entre tendência, composição e operação. O panorama terá um gráfico principal amplo, uma composição circular e uma faixa de decisão com evidências. Os números sempre indicam período e unidade; o seletor de nível muda o conteúdo, sem fingir filtros que a base agregada não permite.

Os níveis O/T/E conservam cinco consultas cada. Cada pergunta tem gráfico apropriado, filtro quando disponível, tabela completa, busca, ordenação e exportação CSV. O público é o gerente municipal: não mostrar OLTP, DW, SQL, códigos de consultas ou parâmetros de algoritmos na interface. Usar linguagem de resultados, atendimento e decisões. A tela de perfis mantém a ressalva sobre Industrial em linguagem simples; o método e os diagnósticos completos ficam nos documentos técnicos. O 5W2H aparece como ações priorizadas com orçamento explicitamente hipotético.

## Interação e acessibilidade

Navegação por botões com estado exposto, contraste, foco visível, labels, tabela semântica, descrições dos gráficos, alternativa de dados, respeito a movimento reduzido e impressão com todos os níveis. A exportação CSV protege células textuais interpretáveis como fórmulas.

## Distribuição

React é compilado e incorporado em `painel.html`, junto com CSS, fonte, dados e imagens. A entrega abre por `file://` sem internet. O servidor local apenas facilita desenvolvimento e apresentação; não muda a origem estática dos dados nem acessa o banco.
