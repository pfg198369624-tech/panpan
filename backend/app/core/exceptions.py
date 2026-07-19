class AppReviewInsightsError(Exception):
    pass


class CollectionError(AppReviewInsightsError):
    pass


class AICallError(AppReviewInsightsError):
    pass


class AISchemaValidationError(AppReviewInsightsError):
    pass


class WorkflowStepError(AppReviewInsightsError):
    pass


class TraceabilityError(AppReviewInsightsError):
    pass
