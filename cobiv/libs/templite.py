import re


class Templite(object):
    delimiter = re.compile(r"\$\{(.*?)\}\$", re.DOTALL)

    def __init__(self, template):
        self.tokens = self.compile(template)

    @classmethod
    def compile(cls, template):
        tokens = []
        for i, part in enumerate(cls.delimiter.split(template)):
            if i % 2 == 0:
                if part:
                    tokens.append((False, part.replace("$\\{", "${")))
            else:
                if not part.strip():
                    continue
                lines = part.replace("}\\$", "}$").splitlines()
                margin = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
                realigned = "\n".join(l[margin:] for l in lines)
                code = compile(realigned, "<templite %r>" % (realigned[:20],), "exec")
                tokens.append((True, code))
        return tokens

    def render(__self, __namespace=None, **kw):
        """
        renders the template according to the given namespace. 
        __namespace - a dictionary serving as a namespace for evaluation
        **kw - keyword arguments which are added to the namespace
        """
        namespace = {}
        if __namespace: namespace.update(__namespace)
        if kw: namespace.update(kw)

        def emitter(*args):
            for a in args: output.append(str(a))

        namespace["write"] = emitter

        output = []
        for is_code, value in __self.tokens:
            if is_code:
                eval(value, namespace)
            else:
                output.append(value)
        return "".join(output)

    # shorthand
    __call__ = render
