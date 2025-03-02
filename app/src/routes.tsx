import { Switch, Route, useHistory, Redirect } from "react-router-dom";
import React from "react";
import LoginPage from "./pages/login";
import LogoutPage from "./pages/logout";

import ClientsPage from "./pages/clients/list";
import ClientPage from "./pages/clients/show";
import ClientEditPage from "./pages/clients/edit";
import ClientNewPage from "./pages/clients/new";
import ClientLegalCasesPage from "./pages/clients/cases";

import LegalCasesPage from "./pages/legalCases/list";
import LegalCasePage from "./pages/legalCases/show";

import MeetingsPage from "./pages/meetings/list";
import MeetingPage from "./pages/meetings/show";
import MeetingEditPage from "./pages/meetings/edit";
import MeetingNewPage from "./pages/meetings/new";

import UserPage from "./pages/users/show";
import UserEditPage from "./pages/users/edit";

import NotFoundPage from "./pages/notFound";
import Navigation from "./components/navigation";
import LogsPage from "./pages/logs/list";

import ReactGA from "react-ga4";
import { hotjar } from "react-hotjar";
import { UserInfo } from "./auth";

if (process.env.REACT_APP_GA_ID) {
  ReactGA.initialize(process.env.REACT_APP_GA_ID!);
}

if (process.env.REACT_APP_HOTJAR_ID && process.env.REACT_APP_HOTJAR_SV) {
  hotjar.initialize(
    Number(process.env.REACT_APP_HOTJAR_ID),
    Number(process.env.REACT_APP_HOTJAR_SV)
  );
}

function Routes() {
  const [id, setId] = React.useState<number>();
  const history = useHistory();
  history.listen((location) => {
    ReactGA.set({ page: location.pathname });
  });

  React.useEffect(() => {
    const userInfo = UserInfo.getInstance();
    const userId = Number(userInfo.getUserId());

    setId(userId);

    if (id! > 0) {
      ReactGA.set({ userId: id });
    }
  }, [id]);

  return (
    <div>
      <Navigation />
      <Switch>
        <Route exact path="/">
          <Redirect to="/login" />
        </Route>
        <Route exact path="/login" component={LoginPage} />
        <Route exact path="/logout" component={LogoutPage} />

        <Route exact path="/clients" component={ClientsPage} />
        <Route exact path="/clients/new" component={ClientNewPage} />
        <Route exact path="/clients/:id" component={ClientPage} />
        <Route exact path="/clients/:id/edit" component={ClientEditPage} />
        <Route
          exact
          path="/clients/:id/cases"
          component={ClientLegalCasesPage}
        />

        <Route exact path="/cases" component={LegalCasesPage} />
        <Route exact path="/cases/:id" component={LegalCasePage} />

        <Route exact path="/meetings" component={MeetingsPage} />
        <Route exact path="/meetings/:id" component={MeetingPage} />
        <Route exact path="/meetings/:id/edit" component={MeetingEditPage} />
        <Route
          exact
          path="/cases/:id/meetings/new"
          component={MeetingNewPage}
        />

        <Route exact path="/users/:id" component={UserPage} />
        <Route exact path="/users/:id/edit" component={UserEditPage} />

        <Route exact path="/updates" component={LogsPage} />

        <Route component={NotFoundPage} />
      </Switch>
    </div>
  );
}

export default Routes;
