function PolicyViewModel(data) {
    var self = this;
    self.id = ko.observable(data.id);
    self.balance = ko.observable(data.balance);
    self.agent = ko.observable(data.agent);
    self.agent_name = ko.observable(data.agent_name);
    self.insured = ko.observable(data.insured);
    self.annual_premium = ko.observable(data.annual_premium);
    self.billing_schedule = ko.observable(data.billing_schedule);
    self.cancel_date = ko.observable(data.cancel_date);
    self.cancel_desc = ko.observable(data.cancel_desc);
    self.effective_date = ko.observable(data.effective_date);
    self.invoices = ko.observableArray(data.invoices);
    self.payments = ko.observableArray(data.payments);
    self.status = ko.observable(data.status);
}

function AppViewModel() {
    var self = this;
    self.policy = ko.observable(new PolicyViewModel(""));
    self.policy_id = ko.observable().extend({ required: true });
    self.policy_date = ko.observable().extend({ required: true });

    self.error_message = ko.observable("");
    self.error = ko.observable(false);
    
    self.search = function () {

        if (this.errors().length > 0) {
            this.errors.showAllMessages();
            return;
        }

        params = self.policy_id() + "/" + self.policy_date();
        self.error(false);

        $.ajax({
            url: '/policy/' + params,
            contentType: 'application/json',
            type: 'GET',
            success: function (data) {
                console.log(data);
                self.policy(new PolicyViewModel(data));
                return;
            },
            error: function (response) {
                console.log(JSON.stringify(response));
                self.error(true);
                self.error_message("There is no policy information corresponding to that id and date");
                self.policy(new PolicyViewModel(""));
                return;
            }
        });
    };
}

appViewModel = new AppViewModel();

appViewModel.errors = ko.validation.group(appViewModel);

appViewModel.requireLocation = function() {
    viewappViewModelModel.location.extend({required: true});
};
ko.applyBindings(appViewModel);