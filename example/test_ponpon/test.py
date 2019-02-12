from miasm.core.positioning import Positioning
import xml.etree.ElementTree as ET


def test_graph(g, nodes, edges):
    g.clear()
    for n in nodes:
        g.new_box(n, height=100, width=70)
    for e in edges:
        g.link_boxes(e[0], e[1])
    g.add_head(0)

    g.auto_arrange_boxes()
    # print(g.boundingbox())


def print_svg(nodes, edges):
    g_plac = Positioning("test")
    test_graph(g_plac, nodes, edges)

    svg_xml = ET.Element("svg")
    svg_xml.set("xmlns:svg", "http://www.w3.org/2000/svg")
    svg_xml.set("version", "1.1")

    g = ET.SubElement(svg_xml, "g")
    g.set("class", "graph")
    g_title = ET.SubElement(g, "title")

    svg = {}
    svg["width"] = 0
    svg["height"] = 0
    svg["node"] = []
    svg["edge"] = []

    n = 0
    for node in nodes:
        node_id = node
        g_node = ET.SubElement(g, "g")
        g_node.set("id", "%s" % str(node_id))
        g_node.set("class", "node")
        n_title = ET.SubElement(g_node, "title")
        n_title.set("id", "%s" % "node"+str(node_id))
        n_title.text = "loc"+str(node_id)
        p_node = ET.SubElement(g_node, "polygon")
        p_node.set("stroke", "transparent")
        p_node.set("style", "fill:#ff99cc")
        box_x = g_plac.box_id[node].x
        box_y = g_plac.box_id[node].y
        box_w = g_plac.box_id[node].w
        box_h = g_plac.box_id[node].h

        loc_text = ET.SubElement(g_node, "text")
        loc_text.text = str("node%s" % node)
        loc_text.set("x", "%s" % str(box_x + 15))
        loc_text.set("y", "%s" % str(box_y + 25))
        loc_text.set("id", "%s" % node)
        loc_text.set("font-size", "14.00")
        loc_text.set("style", "font-family:'Courier New';text-anchor:start;fill:#000000")

        n = n+1
        node_rect = ET.SubElement(g, "rect")
        node_rect.set("id", "%s" % "rect"+str(node_id))
        node_rect.set("style", "fill:none;fill-opacity:1;" +
                      "stroke:#000000;stroke-width:2.83464575;" +
                      "stroke-miterlimit:4;stroke-dasharray:none;" +
                      "stroke-dashoffset:0;stroke-opacity:1")
        node_rect.set("width", "%s" % str(box_w))
        node_rect.set("height", "%s" % str(box_h))
        node_rect.set("x", "%s" % str(box_x))  # Place
        node_rect.set("y", "%s" % str(box_y))  # Place

        node_rect.set("ry", "%s" % str(7))
        #print("Node")
        #print(box_x, box_y, box_w, box_h)
        p_node.set("points",
                   "%s,%s %s,%s %s,%s %s,%s" % (str(box_x),
                                                str(box_y),
                                                str(box_x),
                                                str(box_y + box_h),
                                                str(box_x + box_w),
                                                str(box_y + box_h),
                                                str(box_x + box_w),
                                                str(box_y)))

    for e in edges:
        src = e[0]
        dst = e[1]
        e_path = g_plac.edges[(src, dst)].path
        if len(e_path) < 2:
            continue
        print("EEEDDDDDGGGGEEEE")
        print(e_path)
        g_edge = ET.SubElement(g, "g")
        g_edge.set("id", "edge%s%s" % (str(src), str(dst)))
        g_edge.set("class", "edge")
        title_edge = ET.SubElement(g_edge, "title")
        title_edge.text = "%s to %s" % (str(src),
                                        str(dst))
        line_edge = ET.SubElement(g_edge, "path")
        line_edge.set("fill", "none")
        line_edge.set("stroke", "%s" % "blue")
        arrow_edge = ET.SubElement(g_edge, "polyline")
        arrow_edge.set("fill",  "%s" % "none")
        arrow_edge.set("stroke",  "%s" % "blue")
        arrow_edge.set("stroke-width", "1")

        arrow_edge.set("points", "%s,%s %s,%s %s,%s %s,%s %s,%s %s,%s" % (str(e_path[0][0]),
                                                                          str(e_path[0][1]),
                                                                          str(e_path[0][0]),
                                                                          str(e_path[1][1]),
                                                                          str(e_path[1][0]),
                                                                          str(e_path[1][1]),
                                                                          str(e_path[1][0]),
                                                                          str(e_path[3]),
                                                                          str(e_path[2][0]),
                                                                          str(e_path[3]),
                                                                          str(e_path[2][0]),
                                                                          str(e_path[2][1])))

    s = g_plac.boundingbox()

    svg_xml.set("width", "%spt" % str((s[2] - s[0]) * 2 + 50))
    svg_xml.set("height", "%spt" % str((s[3] - s[1]) * 2 + 50))
    svg_xml.set("viewBox", "%s %s %s %s" % (str(s[0] - 20),
                                            str(s[1] - 20),
                                            str(s[2] - s[0] + 40),
                                            str(s[3] - s[1] + 40)))
    g.set("id", "loc?")
    g_title.set("id", "test")
    g_title.text = "asm_graph"
    out = ET.tostring(svg_xml)
    return out.decode()


list_test = [
    # 0 a->[b,c]->d
    [[0, 1, 2, 3],
     [[0, 1], [0, 2], [2, 3], [1, 3]]],
    # 1 a->[b,c,d]->e
    [[0, 1, 2, 3, 5],
     [[0, 1], [0, 2], [0, 5], [5, 3], [2, 3], [1, 3]]],
    # 2 a->b->c->d
    [[0, 1, 2, 3],
     [[0, 1], [1, 2], [2, 3]]],
    # 3 a->b->c, a->c
    [[0, 1, 2],
     [[0, 1], [1, 2], [0, 2]]],
    # 4 [a,b,c] -> d -> e -> [f,g,h]
    [[0, 1, 2, 3, 4, 5, 6, 7],
     [[0, 3], [1, 3], [2, 3], [3, 4], [4, 5], [4, 6], [4, 7]]],
    # 5 a->[b,c]->[d,e]->f
    [[0, 1, 2, 3, 4, 5],
     [[0, 1], [0, 2], [1, 3], [2, 4], [3, 5], [4, 5]]],
    # 6
    [[0, 1, 2, 3, 4],
     [[0, 1], [1, 2], [2, 3], [2, 4], [3, 1], [3, 4]]],
    # 7
    [[0, 1, 2, 3, 4, 5],
     [[0, 1], [0, 2], [0, 3], [1, 2], [3, 2], [3, 4], [1, 5], [2, 5], [4, 5]]],
    # 8 a->b
    [[0, 1],
     [[0, 1]]],
    # 9
    [[0, 1, 2, 3],
     [[0, 1], [0, 2], [1, 2], [2, 3], [1, 3]]],
    # 10
    [[0, 1, 2, 3],
     [[0, 1], [2, 0], [1, 2], [2, 3], [1, 3]]],
    # 11
    [[0, 1, 2, 3, 4],
     [[0, 4], [4, 1], [1, 2], [2, 3], [1, 3]]],
    # 12
    [[0, 1, 2, 3, 4],
     [[0, 4], [2, 0], [4, 1], [4, 2], [1, 2], [2, 3], [1, 3]]],
    # 13
    [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
     [[0, 1], [0, 2], [1, 6], [2, 3], [3, 4], [4, 5], [4, 8], [6, 7], [6, 8],
      [5, 9], [8, 9], [7, 9], [2, 9], [1, 9]]],
    # 14
    [[0, 1, 2, 3, 4, 5],
     [[0, 1], [0, 2], [1, 3], [2, 4], [1, 5], [2, 5], [3, 5], [4, 5]]],
    # 15
    [[0, 1, 2, 3, 4, 5, 6, 7, 8],
     [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [4, 6], [3, 7], [4, 7], [5, 7],
      [6, 7], [7, 8], [5, 8]]],
    # 16
    [[0, 1, 2, 3, 4, 5],
     [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [3, 4], [4, 5]]],
    # 17
    [[0, 1, 2, 3, 4],
     [[0, 1], [1, 2], [2, 3], [1, 4], [2, 4]]],
    #18
    [[0, 1, 2, 3, 4, 5, 6, 7],
     [[1, 0], [2, 0], [3, 0], [4, 0], [5, 0], [6, 0],
      [1, 3], [2, 4], [3, 5], [4, 6], [7, 1], [7, 2]]],
    #19
    [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
     [[1, 0], [2, 0], [8, 0], [9, 0], [5, 0], [6, 0],
      [1, 3], [2, 4], [3, 5], [4, 6], [6, 8], [5, 9], [7, 1], [7, 2]]],
    #20
    [[0, 1, 2],
     [[0, 1], [1, 2], [1, 1]]
    ],
    #21
    [[0, 1, 2, 3, 4, 5],
     [[0, 1], [1, 2], [1, 3], [1, 4], [2, 1], [3, 1], [4, 1], [2, 5], [4, 5]]
    ],
    #22
    [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
     [[0,1],[0,6],[0,7],[1,2],[1,3],[1,4],[2,11],[3,5],[4,11],[5,11],[6,10],[7,8],[7,9],[8,9],[9,10],[11,10]]
    ],
    #23 caf0
    [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
     [[0,1],[0,2],[1,2],[1,12],[2,3],[2,4],[3,5],[3,7],[4,6],[4,10],[5,7],[5,8],[6,9],[6,10],[7,11],[8,9],[9,10],[10,11],[11,12]]
    ],
]


def test(nb):
    it = 0
    for i in list_test:
        if nb == -1 or nb == it:
            print("Test", it)
            out = open("it%s.svg" % str(it), 'w')
            svg = print_svg(i[0], i[1])
            out.write(svg)
            out.close()
        it += 1


test(-1)
#test(0)
#test(1)
#test(3)
#test(4)
#test(6)
#test(7)
#test(9)
#test(10)
#test(14)
#test(15)
#test(17)
#test(18)
#test(22)
