from django.http import Http404
from django.shortcuts import render, redirect
from vfd_pro.reports.caam.services import (
    handle_client_summary_post,
    get_client_summary_context,
    SESSION_KEY_TMPL,
)


def client_summary(request, client_id: int):
    if request.method == "POST":
        handle_client_summary_post(request.POST, client_id, session=request.session)
        return redirect("caam:client_summary", client_id=client_id)

    saved_state = request.session.get(SESSION_KEY_TMPL.format(client_id=client_id), {})
    context = get_client_summary_context(client_id=client_id, saved_state=saved_state)

    if context is None:
        raise Http404("Client KPI not found")

    return render(request, "caam/client_summary.html", context)
