from future.utils import viewvalues


class Positioning(object):
    groups = []
    edge_dist = 5
    block_dist = 10

    class Box(object):

        def __init__(self, id, content=None):
            self.id = id
            self.x = 0
            self.y = 0
            self.w = 0
            self.h = 0
            self.to = set()
            self.frm = set()
            # only to edges
            self.edges_to = []
            self.edges_frm = []
            self.content = content
            self.move = 1

    class Edge(object):

        def __init__(self, frm, to):
            self.frm = frm
            self.to = to
            self.path = [[0, 0], [0, 0], [0, 0], 0]
            self.posfrm = -1
            self.posto = -1
            self.decx = -1

            self.form = None

    # OK
    def __init__(self, id):
        self.id = id
        self.root_addrs = []
        self.view_x = -0xffffffff
        self.view_y = -0xffffffff
        self.clear()

    def add_head(self, head):
        self.head = self.box_id[head]

    # OK
    def clear(self):
        self.box = []
        self.box_id = {}
        self.edges = {}
        self.original_order = {}

    # OK
    def link_boxes(self, id1, id2):
        assert(self.box_id.get(id1))
        assert(self.box_id.get(id2))
        b1 = self.box_id[id1]
        b2 = self.box_id[id2]
        b1.to.add(b2)
        b2.frm.add(b1)
        edge = self.Edge(b1, b2)
        b1.edges_to.append(edge)
        b2.edges_frm.append(edge)
        self.edges[(id1, id2)] = edge

    # OK
    def new_box(self, id, content=None, height=0, width=0):
        assert(all(b.id != id for b in self.box))
        b = self.Box(id, content=content)
        b.h = height
        b.w = width
        self.box.append(b)
        self.box_id[id] = b
        return b

    # KO to_i: regarder la valeur des element dans self.box
    def boundingbox(self):
        minx_b = min(b.x for b in self.box)
        miny_b = min(b.y for b in self.box)
        maxx_b = max(b.x + b.w for b in self.box)
        maxy_b = max(b.y + b.h for b in self.box)
        if self.edges:
            minx_e = min(min(p[0]
                             if len(e.path) > 0
                             else minx_b for p in e.path[:3])
                         for e in self.edges.values())
            maxx_e = max(max(p[0]
                             if len(e.path) > 0
                             else maxx_b for p in e.path[:3])
                         for e in self.edges.values())
            miny_e = min(min(p[1]
                             if len(e.path) > 0
                             else miny_b for p in e.path[:3])
                         for e in self.edges.values())
            maxy_e = max(max(p[1]
                             if len(e.path) > 0
                             else maxy_b for p in e.path[:3])
                         for e in self.edges.values())

            minx_b = min(minx_b, minx_e)
            miny_b = min(miny_b, miny_e)
            maxx_b = max(maxx_b, maxx_e)
            maxy_b = max(maxy_b, maxy_e)
        return[minx_b, miny_b, maxx_b, maxy_b]

    def pattern_col(self, groups):
        try:
            head = next(g for g in groups if len(g.to) == 1
                        and len(next(iter(g.to)).frm) == 1
                        and (len(g.frm) != 1 or
                             len(next(iter(g.frm)).to) != 1))
            ar = [head]
            while len(head.to) == 1 and len(next(iter(head.to)).frm) == 1:
                head = next(iter(head.to))
                ar.append(head)
            new_box = self.merge_pattern_column(ar)
            # self.fix_edges(new_box)
            return [new_box, ar]
        except StopIteration:
            return [None, []]

    def pattern_line(self, groups):
        for g in groups:
            if (
                    len(g.frm) == 1
                    and len(g.to) <= 1
                    and len(next(iter(g.frm)).to) > 1
            ):
                ar = [gg for gg in next(iter(g.frm)).to
                      if (gg.frm == g.frm and gg.to == g.to)]

            elif (
                    not g.frm
                    and len(g.to) == 1
                    and len(next(iter(g.to)).frm) > 1
            ):
                ar = [gg for gg in next(iter(g.to)).frm
                      if (gg.frm == g.frm and gg.to == g.to)]
            else:
                ar = []
            if len(ar) > 1:
                new_box = self.merge_pattern_line(ar)
                return [new_box, ar]
        if len(ar) <= 1:
            return [None, []]

    def pattern_ifend(self, groups):
        head = None

        for g in groups:
            if len(g.to) == 2:
                g_to = iter(g.to)
                son1 = next(g_to)
                son2 = next(g_to)
                if ((len(son1.frm) == 1 and len(son1.to) == 1
                     and (next(iter(son1.to))) == son2)
                    or (len(son2.frm) == 1 and len(son2.to) == 1
                        and next(iter(son2.to)) == son1)):
                    head = g
                    ar = self.merge_pattern_ifend(head)
                    return [head, [ar]]
                if len(son2.frm) == 1 and len(son1.frm) > 1:
                    tmp = son1
                    son1 = son2
                    son2 = tmp
                if len(son1.frm) == 1 and len(son2.frm) > 1:
                    i = 1
                    list_head = [g]
                    while i < len(son2.frm):
                        if len(son1.to) != 2:
                            break
                        son1_to = list(son1.to)
                        if son1_to[0] == son2:
                            list_head.append(son1)
                            son1 = son1_to[1]
                            i += 1
                        elif son1_to[1] == son2:
                            list_head.append(son1)
                            son1 = son1_to[0]
                            i += 1
                        else:
                            break
                    for elt in son1.frm:
                        if elt == son2:
                            self.merge_pattern_n_ifend(list_head, son2)
                            return [g, []]
        if head is None:
            return [None, []]

    def find_pattern(self, groups):
        [new_box, elts] = self.pattern_col(groups)
        if new_box is None:
            [new_box, elts] = self.pattern_line(groups)
        if new_box is None:
            [new_box, elts] = self.pattern_ifend(groups)
        if new_box is None:
            # self.fix_subgroups(groups)
            return False

        self.fix_xrefs(new_box, elts, groups)

        return True

    def fix_xrefs(self, box, elts, groups):
        # fix xrefs
        for g in box.frm:
            for elt in elts:
                if elt in g.to:
                    g.to.remove(elt)
            g.to.add(box)
        for g in box.to:
            for elt in elts:
                if elt in g.frm:
                    g.frm.remove(elt)
            g.frm.add(box)
        if box not in groups:
            groups[groups.index(elts[0])] = box
        for g in elts:
            if g in list(groups):
                groups.remove(g)
        return True

    def merge_pattern_column(self, ar):
        for i in range(0, len(ar) - 1):
            g = ar[i]
            gn = ar[i+1]
            withchld = [b for b in g.content if b.to]
            if not withchld:
                continue
            wc = withchld[0]
            if (
                    len(withchld) == 1
                    and len(wc.to) >= 1
                    and [elt for elt in wc.to if elt in gn.content] == wc.to
            ):
                tox = min(b.x for b in wc.to)
                toxmax = max(b.x+b.w for b in wc.to)
                # dx1: center wc center around (wc.to.xmin + wc.to.xmax)/2
                dx1 = tox + (toxmax-tox)/2 - (wc.x + wc.w/2)
                # dx2: center wc center around the mean of the centers of wc.to
                dx2 = (sum(b.x + b.w/2 for b in wc.to)
                       / len(wc.to)-(wc.x + wc.w/2))
                dx = (dx1 + dx2) / 2
                for j in range(0, len(ar)):
                    ar[j].w += dx
                    for b in ar[j].content:
                        if j <= i:
                            b.x += dx/2
                        else:
                            b.x += -dx/2

        # moves boxes inside this group
        maxw = max(g.w for g in ar)
        fullh = sum(g.h for g in ar)
        cury = -fullh/2
        for g in ar:
            dy = cury - g.y
            for b in g.content:
                b.y += dy
            cury += g.h

        # create remplacement group
        newg = self.Box(None, [y for x in [g.content for g in ar] for y in x])
        newg.w = maxw
        newg.h = fullh
        newg.x = -newg.w/2
        newg.y = -newg.h/2
        newg.frm = ar[0].frm
        newg.to = ar[len(ar) - 1].to

        return newg

    # OK
    # if a group has no content close to its x/x+w borders, shrink it
    def group_remove_hz_margin(self, g, maxw=16):
        if not g.content:
            if g.x < -maxw/2:
                g.x = -maxw/2
            if g.w > maxw:
                g.w = maxw
            return

        margin_left = min(b.x for b in g.content) - g.x
        margin_right = g.x + g.w - max(b.x + b.w for b in g.content)
        if margin_left + margin_right > maxw:
            g.w -= margin_left + margin_right - maxw
            dx = (maxw/2 + margin_right - margin_left)/2
            for b in g.content:
                b.x = b.x + dx
            g.x = -g.w/2

    # OK
    # a -> [b, c, d] -> e
    def merge_pattern_line(self, ar):
        for g in ar:
            self.group_remove_hz_margin(g)

        # move boxes inside this group
        # ar = ar.sort_by { |g| -g.h }
        maxh = max(g.h for g in ar)
        fullw = sum(g.w for g in ar)
        curx = -fullw/2
        for g in ar:
            # if no to, put all boxes at bottom ; if no frm, put them at top
            if len(g.frm) == 1 and len(g.to) == 0:
                dy = (g.h - maxh)/2
            elif len(g.frm) == 0 and len(g.to) == 1:
                dy = (maxh - g.h)/2
            else:
                dy = 0

            dx = curx - g.x
            for b in g.content:
                b.x += dx
                b.y += dy
            curx += g.w

        # shrink horizontally if possible
        for i in range(len(ar) - 1):
            g1 = ar[i]
            g2 = ar[i + 1]
            if (not g1.content) or (not g2.content):
                # only work with full groups, dont try to interleave gaps see
                # if all of one's boxes can be slightly moved inside the other
                g1ymin = min(b.y - 9 for b in g1.content)
                g1ymax = max(b.y + b.h + 9 for b in g1.content)
                g2ymin = min(b.y - 9 for b in g1.content)
                g2ymax = max(b.y + b.h + 9 for b in g1.content)
                g1_matchg2 = [b for b in g1.content if (b.y + b.h > g2ymin and
                                                        b.y < g2ymax)]
                g2_matchg1 = [b for b in g2.content if (b.y + b.h > g1ymin and
                                                        b.y < g1ymax)]
                if len(g1_matchg2) > 0 and len(g2_matchg1) > 0:
                    g1_up = [b for b in g1.content if b.y + b.h < g2ymin]
                    g1_down = [b for b in g1.content if b.y > g2ymax]
                    g2_up = [b for b in g2.content if b.y + b.h < g1ymin]
                    g2_down = [b for b in g2.content if b.y > g1ymax]
                    # avoid moving into an arrow
                    xmin = max(b.x + b.w + 8 for b in g1_matchg2)
                    xmax = min(b.x - 8 for b in g2_matchg1)

                    if len(g1_up) > 0 and len(g1.down) > 0:
                        xmin = max([xmin].extend((max([b.x + b.w/2 + 8
                                                       for b in g1_up]),
                                                  max([b.x + b.w/2 + 8
                                                       for b in g1_down]))))

                    if len(g2_up) > 0 and len(g2.down) > 0:
                        xmax = min([xmax].extend((min([b.x + b.w/2 + 8
                                                       for b in g2_up]),
                                                  min([b.x + b.w/2 + 8 for
                                                       b in g2_down]))))
                    dx = xmax - xmin
                    if dx > 0:
                        for j in len(ar):
                            for b in ar[j]:
                                if i >= j:
                                    b.x += dx/2
                                else:
                                    b.x += -dx/2

        # add a 'margin-top' proportionnal to the ar width
        # this gap should be relative to the real boxes and not possible
        # previous gaps when merging lines (eg long line + many
        # if patterns -> dont duplicate gaps)
        boxen = [y for x in [g.content for g in ar] for y in x]
        fullw = max(g.x + g.w + 8 for g in boxen) - min(g.x - 8 for g in boxen)
        realh = max(g.y + g.h for g in boxen) - min(g.y for g in boxen)
        if maxh < realh + fullw/4:
            maxh = realh + fullw/4

        # create remplacement group
        newg = self.Box(None, [y for x in [g.content for g in ar] for y in x])
        newg.w = fullw
        newg.h = maxh
        newg.x = -newg.w/2
        newg.y = -newg.h/2
        newg.frm = ar[0].frm
        newg.to = ar[0].to

        return newg

    # OK
    # a -> b -> c & a -> c
    def merge_pattern_ifend(self, head):
        head_to = list(head.to)
        if head_to[1] in head_to[0].to:
            ten = head_to[0]
        else:
            ten = head_to[1]

        # stuff 'then' inside the 'if'
        # move 'if' up, 'then' down
        for g in head.content:
            g.y -= ten.h/2
        for g in ten.content:
            g.y += head.h/2

        head.h += ten.h
        head.y -= ten.h/2

        # widen 'if'
        # this adds a phantom left side
        # drop existing margins first
        self.group_remove_hz_margin(ten)
        dw = ten.w - head.w/2
        if dw > 0:
            # need to widen head to fit ten
            head.w += 2*dw
            head.x -= dw

        for g in ten.content:
            g.x += -ten.x
            head.content.append(g)
        if ten in head.to:
            head.to.remove(ten)
        head_to = list(head.to)
        if ten in head_to[0].frm:
            head_to[0].frm.remove(ten)
        return ten

    def merge_pattern_n_ifend(self, list_head, ten):
        last_son = list_head[len(list_head) - 1]
        for head in list_head:
            if head is not last_son:
                head.to.remove(ten)
                ten.frm.remove(head)
        return

    # OK
    def order_solve_cycle(self, todo, o):
        # 'todo' has no trivial candidate
        # pick one node frmom todo which no other todo can reach
        # exclude pathing through already ordered nodes
        tmp = False
        for t1 in todo:
            for t2 in todo:
                if t1 != t2 and self.can_find_path(t2, t1, dict(o)):
                    tmp = True
            if not tmp:
                return t1

        res = []
        for t1 in todo:
            res.append([t1,
                        len([t2 for t2 in todo if t1 != t2
                             and self.can_find_path(t1, t2, dict(o))]),
                        max(o[gg] for gg
                            in [elt for elt in t1.frm if elt in o])
                        ])
        res.sort(key=lambda x: (x[1], x[2]))
        return res[len(res) - 1][0]

    # OK
    # find the minimal set of nodes from which we can reach all others
    # this is done *before* removing cycles in the graph
    # returns the order (Hash group => group_order)
    # roots have an order of 0
    def order_graph(self, groups, head=None):
        if head:
            roots = [head]
        else:
            roots = [g for g in groups if not g.frm]
        o = {}
        todo = set()

        while(1):
            for g in roots:
                o.setdefault(g, 0)
                todo.update(gg for gg in g.to if gg not in o)
            # order nodes frmom the tentative roots
            while todo:
                try:
                    n = next(g for g in todo if all(gg in o for gg in g.frm))
                except StopIteration:
                    n = self.order_solve_cycle(list(todo), o)
                todo.remove(n)
                o[n] = max(o[g] for g in n.frm if g in o) + 1
                todo.update(g for g in n.to if g not in o)

            if len(o) >= len(groups):
                break

            # Dans le cas ou on a pas recuperer des from
            # pathological cases
            tmp = sorted((g for g in groups
                          if g in o
                          and any(gg not in o for gg in g.frm)),
                         key=lambda x: o[x])
            if tmp:
                noroot = tmp[0]
                # we picked a root in the middle of the graph, walk up
                todo.update(g for g in noroot.frm if g not in o)
                while todo:
                    try:
                        n = next(g for g in todo if all(gg in o
                                                        for gg in g.frm))
                    except StopIteration:
                        n = sorted((elt for elt in todo),
                                   key=lambda x: min(o[gg] for
                                                     gg in [g for g
                                                            in x if g in o]))

                    todo.remove(n)
                    o[n] = min(o[g] for g in [elt for elt
                                              in n.to if elt in o]) - 1

                    todo.update(g for g in n.frm if g in o)
                # setup todo for next fwd iteration
                if not todo:
                    todo.update(g for g in groups
                                if (g not in o and
                                    any(gg in o for gg in g.frm)))
            else:
                # disjoint graph, start over from one other random node
                try:
                    roots.append(next(g for g in groups if g not in o))
                except StopIteration:
                    print("No root anymore")

        # Pas sure peut etre redecaler seulement les layouts
        # Tester avec des graphes qui ne sont pas connexes
        if any(rank < 0 for rank in viewvalues(o)):
            # did hit a pathological case, restart with found real roots
            roots = [g for g in groups
                     if not (any(o[gg] < o[g] for gg in g.frm))]
            o = {}
            todo = set()
            for g in roots:
                o.setdefault(g, 0)
                todo.update(gg for gg in g.to if gg not in o)
            while todo:
                try:
                    n = next(g for g in todo if all(gg in o for gg in g.frm))
                except StopIteration:
                    n = self.order_solve_cycle(todo, o)
                todo.remove(n)
                o[n] = max(o[g] for g in [gg for gg in n.frm if gg in o]) + 1
                todo.update(g for g in n.to if g not in o)
            if len(o) < len(groups):
                return "moo"
        # Original order est mis au debut
        if not self.original_order:
            self.original_order = {x.content[0]: o[x]
                                   for x in o if x.content}
        return o

    def update_original_order(self, order):
        for o in order:
            todo = set()
            todo.add(o)
            while todo:
                elt = todo.pop()
                if elt.content:
                    for content in elt.content:
                        todo.add(content)
                if elt in self.original_order:
                    self.original_order[elt] = order[o]
            print("end")

    def pattern_layout_complex(self, groups):
        order = self.order_graph(groups)

        uniq = None
        groups.sort(key=lambda x: (order[x]))
        for g in groups:
            if len(g.to) <= 1:
                continue
            # list all nodes reachable for every 'to'
            reach = []
            for t in g.to:
                reach.append(self.list_reachable(t))
            uniq = []
            for i in range(len(reach)):
                # take all nodes reachable frmom there ...
                # u = copy(reach[i])
                u = dict(reach[i])
                uniq.append(u)
                # ignore previous layout_complex artifacts
                # u.delete_if { |k, v| k.content.empty? } #TOCHECK
                for j in list(u):
                    if not j.content:
                        del u[j]

                for ii in range(len(reach)):
                    if i == ii:
                        continue
                    # ... and delete nodes reachable frmom anywhere else
                    for l in reach[ii]:
                        if u.get(l):
                            del u[l]
            for u in list(uniq):
                if len(u) <= 1:
                    uniq.remove(u)

            if uniq:
                # now layout every uniq subgroup independently
                for u in uniq:
                    subgroups = [g for g in groups if u.get(g)]

                    # isolate subgroup frmom external links
                    # change all external links into a single empty box
                    newtop = self.Box(None, [])
                    newtop.x = -8
                    newtop.y = -9
                    newtop.w = 16
                    newtop.h = 18
                    newbot = self.Box(None, [])
                    newbot.x = -8
                    newbot.y = -9
                    newbot.w = 16
                    newbot.h = 18
                    hadfrm = []
                    hadto = []
                    for g in subgroups:
                        for t in set(g.to):
                            if u.get(t):
                                continue
                            # if not g in newbot.frm:
                            newbot.frm.add(g)
                            g.to.remove(t)
                            hadto.append(t)
                            # if not newbot in g.to:
                            g.to.add(newbot)
                        for f in set(g.frm):
                            if u.get(f):
                                continue
                            # if not g in newtop.to:
                            newtop.to.add(g)
                            g.frm.remove(f)
                            hadfrm.append(f)
                            # if not newtop in g.frm:
                            g.frm.add(newtop)
                    subgroups.append(newtop)
                    subgroups.append(newbot)

                    # subgroup layout
                    while(len(subgroups) > 1):
                        self.auto_arrange_step(subgroups)
                    newg = subgroups[0]

                    # patch 'groups'
                    idx = -1
                    for i in range(len(groups)):
                        if u.get(groups[i]):
                            idx = i
                            break
                    for g in list(groups):
                        if u.get(g):
                            groups.remove(g)
                    groups[idx:0] = [newg]
                    # restore external links & fix xrefs
                    for f in set(hadfrm):
                        for t in set(f.to):
                            if u.get(t):
                                if t in f.to:
                                    f.to.remove(t)
                        # if not newg in f.to:
                        f.to.add(newg)
                        # if not f in newg.frm:
                        newg.frm.add(f)
                    for t in set(hadto):
                        for f in set(t.frm):
                            if u.get(f):
                                if f in t.frm:
                                    t.frm.remove(f)
                        # if not newg in t.frm:
                        t.frm.add(newg)
                        # if not t in newg.to:
                        newg.to.add(t)

                return True
        return False

    # OK
    # checks if there is a path frmom src to dst avoiding stuff in 'done'
    def can_find_path(self, src, dst, done={}):
        todo = set([src])
        while todo:
            g = todo.pop()
            if done.get(g):
                continue
            if g == dst:
                return True
            done[g] = True
            todo.update(g.to)
        return False

    # OK
    # returns a hash with true for every node reachable frmom src (included)
    def list_reachable(self, src):
        done = {}
        todo = set([src])
        while todo:
            g = todo.pop()
            if done.get(g):
                continue
            done[g] = True
            todo = todo.update(g.to)
        return done

    # OK
    # revert looping edges in groups
    def make_tree(self, groups, order):
        # now we have the roots and node orders
        #  revert cycling edges - o(chld) < o(parent)
        for g in order.keys():
            for gg in set(g.to):
                if order[gg] < order[g]:
                    # cycling edge, revert
                    g.to.remove(gg)
                    gg.frm.remove(g)
                    g.frm.add(gg)
                    gg.to.add(g)

    # OK
    # group groups in layers of same order create dummy groups along
    # long edges so that no path exists between non-contiguous layers
    def create_layers(self, groups, order):
        def newemptybox(groups):
            b = self.Box(None, [])
            b.x = -8
            b.y = -9
            b.w = 16
            b.h = 18
            groups.append(b)
            return b

        newboxo = {}
        for g in order:
            og = order[g]
            # for gg in copy.deepcopy(g.to)
            for gg in set(g.to):
                if order.get(gg):
                    ogg = order[gg]
                elif newboxo.get(gg):
                    ogg = newboxo[gg]
                else:
                    ogg = None
                if ogg > og+1:
                    # long edge, expand
                    sq = [g]
                    for i in range(ogg - 1 - og):
                        sq.append(newemptybox(groups))
                    sq.append(gg)
                    if g in gg.frm:
                        gg.frm.remove(g)
                    if gg in g.to:
                        g.to.remove(gg)
                    if not newboxo.get(g):
                        newboxo[g] = order[g]
                    g1 = sq[0]
                    for g2 in sq:
                        if g2 == g1:
                            continue
                        # if not g2 in g1.to:
                        g1.to.add(g2)
                        # if not g1 in g2.frm:
                        g2.frm.add(g1)
                        newboxo[g2] = newboxo[g1]+1
                        g1 = g2
                    if newboxo[gg] != ogg:
                        print("Error")
        order.update(newboxo)
        # TODO
        # layers[o] = [list of nodes of order o]
        len_layers = max(value for value in viewvalues(order))
        layers = [None] * (len_layers + 1)

        for g in groups:
            if not layers[order[g]]:
                layers[order[g]] = []
            layers[order[g]].append(g)
        return layers

    # take all groups, order them by order, layout as layers
    # always return a single group holding everything
    def layout_layers(self, groups):
        order = self.order_graph(groups)
        # already a tree
        layers = self.create_layers(groups, order)
        if not layers:
            return False

        for l in layers:
            if l:
                for g in l:
                    self.group_remove_hz_margin(g)

        # widest layer width
        maxlw = max([sum(g.w for g in l) for l in layers if l])

        # center the 1st layer boxes on a segment that large
        x0 = maxlw/2.0
        curlw = sum(g.w for g in layers[0])
        dx0 = (maxlw - curlw) / (2.0*len(layers[0]))
        for g in layers[0]:
            x0 += dx0
            g.x = x0
            x0 += g.w + dx0

        # at this point, the goal is to reorder the most populated layer
        # the best we can, and move other layers' boxes accordingly
        for l in range(1, len(layers)):
            # for each subsequent layer, reorder boxes
            # based on their ties with the previous layer
            i = 0
            res = []
            for g in layers[l]:
                # we know g.frmom is not empty (g would be in @layer[0])
                # medfrm = (reduce(lambda a, b: a + b,
                # ((gg.x + gg.w)/2.0 for gg in g.frm)) / len(g.frm))
                tmp = 0
                for gg in g.frm:
                    tmp += (gg.x + gg.w)/2
                medfrm = tmp / (len(g.frm))
                res.append([g, medfrm, i])
            # on ties, keep original order
            res.sort(key=lambda x: (x[1], x[2]))
            layers[l] = [elt[0] for elt in res]

            # now they are reordered, update their #x accordingly
            # evenly distribute them in the layer
            x0 = maxlw/2.0
            curlw = sum(g.w for g in layers[l])
            dx0 = (maxlw - curlw) / (2.0*len(layers[l]))
            for g in layers[l]:
                x0 += dx0
                g.x = x0
                x0 += g.w + dx0

        # for l in range(0, len(layers)):
        for l in range(len(layers) - 1, -1, -1):
            # for each subsequent layer, reorder boxes
            # based on their ties with the previous layear
            i = 0
            res = []
            for g in layers[l]:
                # TODO floating end
                if not g.to:
                    medfrm = 0
                else:
                    tmp = 0
                    for gg in g.to:
                        tmp += (gg.x + gg.w)/2.0
                    medfrm = tmp / (len(g.to))
                # on ties, keep original order
                res.append([g, medfrm, i])
            res.sort(key=lambda x: (x[1], x[2]))

            layers[l] = [elt[0] for elt in res]

            # now they are reordered, update their #x accordingly
            x0 = maxlw/2.0
            curlw = sum(g.w for g in layers[l])
            dx0 = (maxlw - curlw) / (2.0*len(layers[l]))
            for g in layers[l]:
                x0 += dx0
                g.x = x0
                x0 += g.w + dx0

        # now the boxes are (hopefully) sorted correctly position them
        # according to their ties with prev/next layer from the maxw layer
        # (positionning = packed), propagate adjacent layers positions
        try:
            maxidx = next(i for i in range(0, len(layers))
                          if (sum(g.w for g in layers[i]) == maxlw))
        except StopIteration:
            print("Problem")

        # list of layer indexes to walk
        ilist = [maxidx]
        if maxidx < len(layers) - 1:
            ilist.extend([i for i in range(maxidx+1, len(layers))])
        if maxidx > 0:
            ilist.extend([i for i in range(maxidx-1, -1, -1)])

        layerbox_tmp = {}
        for i in ilist:
            layer = layers[i]
            curlw = sum(g.w for g in layer)
            # left/rightmost acceptable position for the
            # current box w/o overflowing on the right side
            minx = -maxlw/2.0
            maxx = minx + (maxlw-curlw)
            # replace whole layer with a box
            newg = self.Box(None, [y for x in
                                   [g.content for g in layer] for y in x])
            if layerbox_tmp.get(i):
                layerbox_tmp[i].append(newg)
            else:
                layerbox_tmp[i] = newg
            newg.w = maxlw
            newg.h = max(g.h for g in layer)
            newg.x = -newg.w/2
            newg.y = -newg.h/2
            # dont care for frmom/to, we'll return a single box anyway

            for g in layer:
                if i < maxidx:
                    ref = list(g.to)
                else:
                    ref = list(g.frm)
                # TODO elastic positionning around the ideal position
                # (g and g+1 may have the same med, then center both on it)
                if i == maxidx:
                    nx = minx
                elif not ref:
                    nx = (minx+maxx)/2
                else:
                    # center on the outline of rx
                    # may want to center on rx center's center ?
                    ref.sort(key=lambda a: (a.x))
                    rx = list(ref)
                    med = (rx[0].x +
                           rx[len(rx)-1].x +
                           rx[len(rx)-1].w - g.w) / 2.0
                    nx = min([max([med, minx]), maxx])

                dx = nx+g.w/2
                for b in g.content:
                    b.x += dx
                minx = nx+g.w
                maxx += g.w

        layerbox = []

        max_layerbox = max(iter(layerbox_tmp))
        for i in range(0, max_layerbox + 1):
            layerbox.append(layerbox_tmp[i])
        newg = self.Box(None, [y for x in
                               [g.content for g in layerbox] for y in x])
        newg.w = max(g.w for g in layerbox)
        newg.h = sum(g.h for g in layerbox)
        newg.x = -newg.w/2
        newg.y = -newg.h/2

        # vertical: just center each box on its layer
        y0 = newg.y
        for lg in layerbox:
            for b in lg.content:
                b.y += y0-lg.y
            y0 += lg.h

        while groups:
            groups.pop()
        groups.extend([newg])

    # place boxes in a good-looking layout
    # create artificial 'group' container for boxes,
    # that will later be merged in geometrical patterns
    def auto_arrange_init(self):
        # 'group' is an array of boxes
        # all groups are centered on the origin
        h = {}  # { box => group }
        self.groups = []
        for b in self.box:
            b.x = -b.w/2
            b.y = -b.h/2
            g = self.Box(0, content=[b])
            g.x = b.x - 20
            g.y = b.y - 22
            g.w = b.w + 40
            g.h = b.h + 44
            # h[g] = b
            h[b] = g
            self.groups.append(g)
        # init group.to/frmom
        # must always point to something that is in the 'groups' array
        # no self references
        # a box is in one and only one group in 'groups'
        for g in self.groups:
            g.to = set(h[t] for t in g.content[0].to
                       if h[t] != g and h[t] is not None)
            g.frm = set(h[f] for f in g.content[0].frm
                        if h[f] != g and h[f] is not None)
        order = self.order_graph(self.groups)
        # remove cycles frmom the graph
        self.make_tree(self.groups, order)

    # def auto_arrange_step(self, groups=self.igroups):
    def auto_arrange_step(self, groups):
        return (
            self.find_pattern(groups)
            or self.pattern_layout_complex(groups)
            or self.layout_layers(groups)
        )

    def auto_arrange_post(self):
        self.auto_arrange_movebox()
        # auto_arrange_vertical_shrink

    # actually move boxes inside the groups
    def auto_arrange_movebox(self):
        for g in self.groups:
            dx = int((g.x + g.w/2))
            dy = int((g.y + g.h/2))
            for b in g.content:
                b.x += dx
                b.y += dy

    def auto_arrange_vertical_shrink(self):
        # vertical shrink
        # TODO stuff may shrink vertically more if we could
        # move it slightly horizontally...
        self.box.sort(key=lambda b: (b.y))
        for b in self.box:
            if not b.frm:
                continue
            # move box up to its frmom, unless something blocks the way
            min_y = max([by for by in
                         [bb.y+bb.h for bb in b.frm] if by <= b.y])
            moo = []
            moo << 8*len(b.frm)
            moo << 8*len(b.frm[0].to)
            cx = b.x+b.w/2
            moo.append(max([(cx - (bb.x+bb.w/2)).abs for bb in b.frm]) / 10)
            cx = b.frm[0].x+b.frm[0].w/2
            moo.append(max([(cx - (bb.x+bb.w/2)).abs
                            for bb in b.frm[0].to]) / 10)
            margin_y = 16 + moo.max

            if (not min_y) or b.y <= min_y + margin_y:
                continue

            blocking = [bb for bb in self.box if (
                bb != b
                and bb.y+bb.h > min_y
                and bb.y+bb.h < b.y
                and bb.x-12 < b.x+b.w
                and bb.x+bb.w+12 > b.x
            )]
            may_y = [bb.y+bb.h for bb in blocking].append(min_y)
            try:
                # should not collision with b if moved to by+margin_y
                do_y = next(by for by in [by + margin_y for by in may_y].sort()
                            if not (any(bb.x-12 < b.x+b.w
                                    and bb.x+bb.w+12 > b.x
                                    and bb.y-12 < by+b.h
                                    and bb.y+bb.h+12 > by for bb in blocking)))
            except StopIteration:
                print("Error")

            if do_y < b.y:
                b.y = do_y

            # no need to re-sort outer loop

        # TODO
        # energy-minimal positionning of boxes frmom this basic layout
        # avoid arrow confusions

    def node_zone(self, order):
        res = []
        for k in self.original_order.keys:
            res.append([k.x, k.w, k.w, k.h])
        return res

    def get_box_leafs(self, box):
        todo = {box}
        res = set()
        while todo:
            b = todo.pop()
            for g in b.content:
                if g in self.original_order:
                    res.add(g)
                elif g.content:
                    todo.add(g)
        return res

    def get_config_edges(self, b):
        nb_et = len(b.edges_to)
        nb_ef = len(b.edges_frm)
        if nb_et > 1:
            ex_t = (b.x + (b.w/2)) - 20
            interxt = 40/(nb_et-1)
        else:
            ex_t = b.x + (b.w/2)
            interxt = 0
        if nb_ef > 1:
            ex_f = (b.x + (b.w/2)) - 20
            interxf = 40/(nb_ef-1)
        else:
            ex_f = b.x + (b.w/2)
            interxf = 0
        ey_t = b.y + b.h
        ey_f = b.y
        return [nb_et, ex_t, ey_t, interxt, nb_ef, ex_f, ey_f, interxf]

    def pass_on_block(self, e, loop=False):
        ex_t = e.path[0][0]
        if loop:
            n_to = self.original_order[e.frm] + 1
            n_frm = self.original_order[e.to] - 1
        else:
            n_to = self.original_order[e.to]
            n_frm = self.original_order[e.frm]

        conflict_block = [x for x in self.original_order
                          if (self.original_order[x] > n_frm
                              and self.original_order[x] < n_to
                              and x != e.to and x != e.frm)]

        if loop:
            conflict_block.append(e.to)
            conflict_block.append(e.frm)

        # Put all the conflict_block in the unused_range
        unused_range = [(int(b.x) - self.block_dist,
                         int(b.x + b.w)+self.block_dist)
                        for b in conflict_block]

        # Add the edge on the unused_range
        for b in self.original_order:
            if b is not (e.frm or e.to):
                for tmp_e in b.edges_to:
                    if (
                        (self.original_order[tmp_e.frm] >=
                         self.original_order[e.frm]
                         and self.original_order[tmp_e.frm] <
                         self.original_order[e.to])
                        or (self.original_order[tmp_e.to] >= e.frm
                            and self.original_order[tmp_e.to] < e.to)
                        or (self.original_order[tmp_e.frm] <=
                            self.original_order[e.frm]
                            and self.original_order[tmp_e.to] >=
                            self.original_order[e.to])
                    ):
                        unused_range.append((int(tmp_e.path[0][0]) -
                                             self.edge_dist,
                                             int(tmp_e.path[0][0]) +
                                             self.edge_dist))
                        unused_range.append((int(tmp_e.path[1][0]) -
                                             self.edge_dist,
                                             int(tmp_e.path[1][0]) +
                                             self.edge_dist))
                        unused_range.append((int(tmp_e.path[2][0]) -
                                             self.edge_dist,
                                             int(tmp_e.path[2][0]) +
                                             self.edge_dist))

        # Test if there is a cross between the current edge
        # and the unused_range
        if (self.test_elt_not_in_list_range(int(ex_t), unused_range)
            and self.test_elt_not_in_list_range(int(ex_t)+1,
                                                unused_range)):
            print(unused_range)
            print(int(ex_t))
            return 0

        # Regarde s'il y a un espace entre ex_t et les block a gauche
        ex_t_int = int(ex_t)
        max_left = int(max(r[1] for r in unused_range))
        min_left = int(min(r[0] for r in unused_range))

        newx = 0
        for i in range(ex_t_int, max_left + 1):
            if self.test_elt_not_in_list_range(i, unused_range):
                newx = i - ex_t
                break

        for i in range(ex_t_int, min_left - 1):
            if self.test_elt_not_in_list_range(i, unused_range):
                tmp_newx = ex_t - abs(i)
                if abs(newx) < abs(tmp_newx):
                    return newx
                else:
                    return tmp_newx
        return newx

    def test_elt_not_in_list_range(self, elt, list_range):
        for r in list_range:
            if elt in range(r[0], r[1]):
                return False
        return True

    def check_edge_to(self, e, pos, config, simple=False, loop=False):
        ex_t = config[1] + pos * config[3]
        ey_t = config[2]
        e.posto = pos
        e.path[0] = [ex_t, ey_t]
        e.path[1] = [ex_t, ey_t]
        if not simple:
            # si on a une boucle
            if self.original_order[e.frm] > self.original_order[e.to]:
                print("Boucle")
                print(e.path)
                decx = self.pass_on_block(e, loop=True)
                print(decx)
                e.decx = decx
                e.path[1] = [ex_t + e.decx, ey_t]
                print(e.path)
            # si on a une loop sur un block
            elif e.frm == e.to:
                e.path[1] = [e.frm.x + e.frm.w + 10, ey_t]
            if not loop:
                # si on a plus d'un niveau d'écart
                if(self.original_order[e.frm] < self.original_order[e.to] - 1):
                    print("Double niveau")
                    print(e.path)
                    decx = self.pass_on_block(e)
                    print(decx)
                    e.decx = decx
                    e.path[1] = [ex_t + e.decx, ey_t]
                    print(e.path)

    def check_edge_frm(self, e, pos, config, simple=False):
        ex_f = config[5] + pos * config[7]
        ey_f = config[6]
        # if not simple:
        #     if((self.original_order[e.frm] == self.original_order[e.to] - 1)
        #        or (self.original_order[e.frm] == self.original_order[e.to]
        #            and e.frm != e.to)):
        #         e.path[1] = [ex_f, ey_f]
        #     else:
        #         if len(e.path) == 2:
        #             e.path.insert(2, [ex_f, ey_f])
        #         else:
        #             e.path[2] = [ex_f, ey_f]
        # else:
        e.path[2] = [ex_f, ey_f]
        e.posfrm = pos

    def auto_fix_pos_edge(self, simple=False, loop=False, cross_edge=False):
        print("Block")
        print(self.original_order)
        for b in self.original_order:
            if cross_edge:
                b.edges_to.sort(key=lambda x: (x.path[1][0]))
                b.edges_frm.sort(key=lambda x: (x.path[1][0]))
            else:
                b.edges_to.sort(key=lambda x: (x.to.x))
                b.edges_frm.sort(key=lambda x: (x.frm.x))
            config = self.get_config_edges(b)
            posto = 0
            for e in b.edges_to:
                if e.to in self.original_order:
                    self.check_edge_to(e, posto, config, simple, loop)
                posto += 1
            posfrm = 0
            for e in b.edges_frm:
                if e.frm in self.original_order:
                    self.check_edge_frm(e, posfrm, config, simple)
                posfrm += 1

    def auto_set_y(self, top=True):
        for b in self.original_order:
            if top:
                y0 = b.y + b.h + self.block_dist

                # Regle le probleme des blocks sur le meme level
                for block in self.original_order:
                    if self.original_order[b] == self.original_order[block]:
                        for e1 in b.edges_to:
                            for e2 in block.edges_to:
                                if e1.to == e2.to:
                                    if b.x < block.x and b.x < e1.to.x:
                                        y0 = y0 + ((len(block.edges_to)+1)
                                                   * self.edge_dist)
                                    elif b.x > block.x and b.x >= e1.to.x:
                                        y0 = y0 + ((len(block.edges_to)+1)
                                                   * self.edge_dist)

                edges_left = [e for e in b.edges_to
                              if e.path[1][0] < e.path[0][0]]
                edges_right = [e for e in b.edges_to
                               if e.path[1][0] >= e.path[0][0]]
                # Devide the edges from left and right edges
                edges_left.sort(key=lambda e: (e.path[0][0]))
                edges_right.sort(key=lambda e: (e.path[0][0]), reverse=True)
            else:
                y0 = b.y - self.block_dist
                edges_left = [e for e in b.edges_frm
                              if e.path[2][0] < e.path[1][0]]
                edges_right = [e for e in b.edges_frm
                               if e.path[2][0] >= e.path[1][0]]
                # Devide the edges from left and right edges
                edges_left.sort(key=lambda e: (e.path[2][0]), reverse=True)
                edges_right.sort(key=lambda e: (e.path[2][0]))

            # Place the first part of the edges
            y_tmp = y0
            for e in edges_left:
                if top:
                    e.path[1][1] = y_tmp
                    y_tmp += self.edge_dist
                else:
                    e.path[3] = y_tmp
                    y_tmp -= self.edge_dist
            y_tmp = y0
            for e in edges_right:
                if top:
                    if e.path[0][0] == e.path[1][0]:
                        e.path[3] = y_tmp
                    else:
                        e.path[1][1] = y_tmp
                    y_tmp += self.edge_dist
                else:
                    if e.path[0][0] != e.path[1][0]:
                        e.path[3] = y_tmp
                        y_tmp -= self.edge_dist

    # def auto_check_edge_superposition(self):
    #     self.y_used_left = {}
    #     self.y_used_right = {}
    #     # print(self.original_order)
    #     for b in self.original_order:
    #         # print(b)
    #         block_order = self.original_order[b]

    #         # Edge arriving on the block
    #         to_check = [e for e in b.edges_frm if len(b.edges_frm) >= 2]
    #         # Edge with siblinks
    #         for elt in b.frm:
    #             for e in elt.edges_to:
    #                 if self.original_order[e.to] == block_order and e.to != b:
    #                     to_check.append(e)

    #         if len(b.edges_frm) < 2:
    #             for e in b.edges_frm:
    #                 if e not in to_check:
    #                     e.path[3] = e.path[2][1] - self.edge_dist*2
    #                 continue

    #         self.indent_left = self.edge_dist
    #         self.indent_right = self.edge_dist

    #         for e in to_check:
    #             if self.original_order[e.frm] >= self.original_order[e.to]:
    #                 n_to = self.original_order[e.frm] + 1
    #                 n_frm = self.original_order[e.to] - 1
    #                 conflict_box = []
    #             else:
    #                 n_to = self.original_order[e.to]
    #                 n_frm = self.original_order[e.frm]

    #                 print(n_to)
    #                 print(n_frm)
    #                 # Prendre le min des blocs suivants
    #                 conflict_box = [(int(elt.y),
    #                                  int(elt.x) + self.block_dist,
    #                                  int(elt.x + elt.y) + self.block_dist)
    #                                 for elt in self.original_order
    #                                 if (self.original_order[elt] > n_frm
    #                                     and self.original_order[elt] < n_to
    #                                     and elt != e.to and elt != e.frm)]

    #             y0 = e.path[2][1]
    #             if e.path[1][0] <= e.path[2][0]:
    #                 y0 = y0 - self.indent_left
    #             else:
    #                 y0 = y0 - self.indent_right

    #             print("Yo")
    #             print(e.path)
    #             print(conflict_box)

    #             test_conflict = [elt[0] for elt in conflict_box
    #                              if e.path[2][0] > elt[1]
    #                              and e.path[2][0] < elt[2]]
    #             if test_conflict:
    #                 print("Conflict")
    #                 y0 = min(test_conflict) - self.block_dist

    #             y0 -= y0 % self.edge_dist
    #             e.path[3] = y0
    #             self.set_height(e.path)

    def auto_arrange_edges(self):
        # Set src and dest for all edges
        # First fix simple edge
        # self.auto_fix_pos_edge(simple=True)
        # Then fix loop
        # self.auto_fix_pos_edge(simple=True, loop=True)
        # Then all the other cases
        self.auto_fix_pos_edge()

        # Replace les edges à la sortie des boîtes pour ne
        # pas avoir de croisements
        self.auto_fix_pos_edge(cross_edge=True)
        # The 2 previous func deal with x now deal with y
        # Permet aux fleches qui arrivent sur une même box de ne
        # pas se surperposer
        self.auto_set_y()
        self.auto_set_y(top=False)
        # self.auto_check_edge_superposition()

    def set_height(self, path):
        x0 = path[1][0]
        x1 = path[2][0]
        y1 = path[3]

        if x0 > x1:
            y_used = self.y_used_right
            nb_used = self.indent_right
        else:
            y_used = self.y_used_left
            nb_used = self.indent_left

        if y1 in y_used:
            tmp = y_used[y1]
            tmp_x0 = tmp[1][0]
            if x0 > x1:
                if x0 <= tmp_x0:
                    path[3] = y1 - nb_used
                    self.set_height(path)
                else:
                    y_used[y1] = path
                    tmp[3] = y1 - nb_used
                    self.set_height(tmp)
            else:
                if x0 >= tmp_x0:
                    path[3] = y1 - nb_used
                    self.set_height(path)
                else:
                    y_used[y1] = path
                    tmp[3] = y1 - nb_used
                    self.set_height(tmp)
        else:
            y_used[y1] = path

    def auto_arrange_boxes(self):
        self.auto_arrange_init()
        while len(self.groups) > 1 and self.auto_arrange_step(self.groups):
            None
        self.auto_arrange_post()
        self.auto_arrange_edges()
        self.groups = []
