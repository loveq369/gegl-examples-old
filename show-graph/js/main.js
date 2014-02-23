var g = new dagre.Digraph();

var json_data = '{"children": {"input": {"children": {}, "label": "gegl:rectangle"}, "aux": {"children": {"input": {"children": {}, "label": "gegl:buffer-source"}, "aux": {"children": {"input": {"children": {"input": {"children": {"aux": {"children": {}, "label": "gegl:rectangle"}}, "label": "gegl:add"}, "aux": {"children": {"input": {"children": {}, "label": "gegl:buffer-source"}, "aux": {"children": {}, "label": "gegl:rectangle"}}, "label": "gegl:add"}}, "label": "svg:src-over"}}, "label": "gegl:opacity"}}, "label": "svg:src-over"}}, "label": "svg:src-over"}';

var data = JSON.parse(json_data);

function parse(data) {
    var label = data.label;
    var node = g.addNode(null, {label: label});

    if ("children" in data) {
        for (var i in data.children) {
            var child = parse(data.children[i]);
            g.addEdge(null, child, node, {label: i});
        }
    }
    return node;
};
parse(data);

var renderer = new dagreD3.Renderer();
var layout = dagre.layout().rankDir("BT");
renderer.layout(layout);
renderer.edgeTension(0);
renderer.run(g, d3.select("svg g"));
