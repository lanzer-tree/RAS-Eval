/**
 * @file nuxmv.h
 *
 * @mainpage Software Description Document
 *
 * This is the Software Description Document (SDD) for the C API to
 * [nuXmv](https://nuxmv.fbk.eu), a symbolic model checker
 * for the analysis of synchronous finite-state and infinite-state systems.
 *
 * The document is composed of the following sections:
 * - [Data Structures](annotated.html) shows a sorted list of data types.
 * - [Topics](topics.html) follows the structure of the header file @ref nuxmv.h
 *   and presents the data types and functions available to the programmer.
 * - [Unimplemented Functions](unimplemented.html) shows a list of functions
 *   which are available through the API but that will be available in future
 *   releases.
 *
 *
 * @author
 *     Fondazione Bruno Kessler <[https://www.fbk.eu/](fbk.eu)>
 * @date
 *     @showdate
 * @copyright
 *     You may study, copy, compile and execute this Software only for academic,
 *     non-commercial research purposes, subject to the restrictions in the
 *     LICENSE.txt that accompanies the Software.
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>

/**
 * @brief Macro for counting the number of elements of an array
 *
 * @param[in] array
 *     The array to count the element of.
 * @return
 *     The number of elements in the array.
 */
#define NUXMV_COUNT_OF(array) (sizeof(array) / sizeof(array[0]))

/**
 * @brief Status codes
 *
 * These codes are used to check the success/failure of API calls.
 *
 */
typedef enum nuxmv_status_code {
    /** The called API function failed. */
    NUXMV_FAILURE = 0,
    /** The called API function succeeded. */
    NUXMV_SUCCESS
} nuxmv_status_code;

/** *************************************************************************
 * @defgroup nuxmv_group_structs Data Structures
 *
 * @brief All data types used by the API
 *
 * This section lists all data types.
 */
///@{

/**
 * @brief Environment object
 *
 * @sa
 * -  nuxmv_create_env()
 */
typedef struct nuxmv_env {
    /** Opaque pointer representing an environment. */
    void *repr;
} nuxmv_env;

/** @brief Option object as key-value pair */
typedef struct nuxmv_opt {
    /** Null-terminated string representing the option name. */
    const char *key;
    /** Null-terminated string representing the value for the option. */
    const char *value;
} nuxmv_opt;

/**
 * @brief Expression type object
 *
 * @sa
 * - @ref nuxmv_make_boolean_type()
 * - @ref nuxmv_make_integer_type()
 * - @ref nuxmv_make_real_type()
 * - @ref nuxmv_make_enum_type()
 * - @ref nuxmv_make_set_type()
 * - @ref nuxmv_make_signed_word_type()
 * - @ref nuxmv_make_unsigned_word_type()
 * - @ref nuxmv_make_array_type()
 * - @ref nuxmv_make_function_type()
 */
typedef struct nuxmv_expr_type {
    /** Opaque pointer representing an expression type. */
    void *repr;
} nuxmv_expr_type;

/**
 * @brief Tags for expression types
 *
 * @sa
 * - @ref nuxmv_expr_type
 * - @ref nuxmv_expr_type_get_tag()
 */
typedef enum nuxmv_expr_type_tag {
    NUXMV_TYPE_INVALID = -1,  /**< Not a valid type. */
    NUXMV_TYPE_BOOL,          /**< Boolean type. */
    NUXMV_TYPE_INT,           /**< Unbound integer type. */
    NUXMV_TYPE_REAL,          /**< Real type. */
    NUXMV_TYPE_ENUM,          /**< Symbolic enumerative type */
    NUXMV_TYPE_SET,           /**< Set type. */
    NUXMV_TYPE_SIGNED_WORD,   /**< Signed word type. */
    NUXMV_TYPE_UNSIGNED_WORD, /**< Unsigned word type. */
    NUXMV_TYPE_ARRAY,         /**< Array type. */
    NUXMV_TYPE_FUNCTION,      /**< Function type. */
    NUXMV_TYPE_LAST_          /**< (List terminator.) */
} nuxmv_expr_type_tag;

/**
 * @brief Variable type object
 *
 * @sa
 * - @ref nuxmv_make_simple_var_type()
 * - @ref nuxmv_make_var_type_with_domain()
 * - @ref nuxmv_make_var_type_with_integer_range()
 * - @ref nuxmv_make_var_type_array()
 */
typedef struct nuxmv_var_type {
    /** Opaque pointer representing a variable type. */
    void *repr;
} nuxmv_var_type;

typedef enum nuxmv_var_type_tag {
    NUXMV_VAR_TYPE_INVALID = -1,
    NUXMV_VAR_TYPE_BOOL,          /**< Boolean type. */
    NUXMV_VAR_TYPE_INT,           /**< Unbound integer type. */
    NUXMV_VAR_TYPE_REAL,          /**< Real type. */
    NUXMV_VAR_TYPE_ENUM,          /**< Symbolic enumerative type */
    NUXMV_VAR_TYPE_INT_ENUM,      /**< Integer enumerative type */
    NUXMV_VAR_TYPE_INT_RANGE,     /**< Bound integer type. */
    NUXMV_VAR_TYPE_SIGNED_WORD,   /**< Signed word type. */
    NUXMV_VAR_TYPE_UNSIGNED_WORD, /**< Unsigned word type. */
    NUXMV_VAR_TYPE_ARRAY,         /**< Array type. */
    NUXMV_VAR_TYPE_FUNCTION,      /**< Function type. */
    NUXMV_VAR_TYPE_LAST_
} nuxmv_var_type_tag;

/**
 * @brief Symbol object
 *
 * @sa
 * - @ref nuxmv_make_symbol()
 * - @ref nuxmv_make_scoped_symbol()
 */
typedef struct nuxmv_symbol {
    /** Opaque pointer representing a symbol. */
    void *repr;
} nuxmv_symbol;

/**
 * @brief Expression object
 *
 * @sa
 * - @ref nuxmv_make_identifier()
 * - @ref nuxmv_make_value()
 * - @ref nuxmv_make_op()
 * - @ref nuxmv_make_expr_from_string()
 * - @ref nuxmv_simplify_expr()
 */
typedef struct nuxmv_expr {
    /** Opaque pointer representing an expression. */
    void *repr;
} nuxmv_expr;

/**
 * @brief Operators
 *
 * @sa
 * - @ref nuxmv_expr_get_op_tag()
 * - @ref nuxmv_expr_contains_temporal_operators()
 */
typedef enum nuxmv_op_tag {
    NUXMV_OP_INVALID = -1, /**< Not a valid operator. */
    NUXMV_OP_AND,          /**< Logical conjunction operator. */
    NUXMV_OP_OR,           /**< Logical disjunction operator. */
    NUXMV_OP_NOT,          /**< Logical negation operator. */
    NUXMV_OP_XOR,          /**< Logical exclusive disjunction operator. */
    NUXMV_OP_XNOR,         /**< Logical exclusive NOR operator. */
    NUXMV_OP_IMPLIES,      /**< Logical conditional operator. */
    NUXMV_OP_IFF,          /**< Logical biconditional operator. */

    NUXMV_OP_EQ,  /**< Equal to operator. */
    NUXMV_OP_NEQ, /**< Not equal to operator. */
    NUXMV_OP_GT,  /**< Greater than operator. */
    NUXMV_OP_GTE, /**< Greater than or equal to operator. */
    NUXMV_OP_LT,  /**< Less than operator. */
    NUXMV_OP_LTE, /**< Less than or equal to operator. */

    NUXMV_OP_NEGATIVE_NUM, /**< Negative number sign. (car(n) is the number) */
    NUXMV_OP_PLUS,         /**< Addition operator. */
    NUXMV_OP_MINUS,        /**< Subtraction operator. */
    NUXMV_OP_TIMES,        /**< Multiplication operator. */
    NUXMV_OP_DIV,          /**< Division operator. */
    NUXMV_OP_MOD,          /**< Modulo operator. */
    NUXMV_OP_LSHIFT,       /**< Left shift operator. */
    NUXMV_OP_RSHIFT,       /**< Right shift operator. */

    NUXMV_OP_ABS,   /**< Absolute operator. */
    NUXMV_OP_ACOS,  /**< Arccosine function (acos(x)). */
    NUXMV_OP_ASIN,  /**< Arcsine function (asin(x)). */
    NUXMV_OP_ATAN,  /**< Arctangent function (atan(x)). */
    NUXMV_OP_COS,   /**< Cosine operator. */
    NUXMV_OP_EXP,   /**< Euler's number exponentiation operator. */
    NUXMV_OP_FLOOR, /**< Floor operator. */
    NUXMV_OP_LN,    /**< Natural logarithm operator. */
    NUXMV_OP_MAX,   /**< Maximum operator. */
    NUXMV_OP_MIN,   /**< Minimum operator. */
    NUXMV_OP_PI,    /**< Pi constant. */
    NUXMV_OP_POW,   /**< Exponentiation operator. */
    NUXMV_OP_SIN,   /**< Sine operator. */
    NUXMV_OP_SQRT,  /**< Square root function (sqrt(x)). */
    NUXMV_OP_TAN,   /**< Tangent operator. */

    NUXMV_OP_NEXT_FUNCTION, /**< next function. */

    NUXMV_OP_GLOBALLY, /**< Globally temporal operator. */
    NUXMV_OP_FINALLY,  /**< Finally temporal operator. */
    NUXMV_OP_NEXT,     /**< Next temporal operator.  */
    NUXMV_OP_UNTIL,    /**< Until temporal operator. */
    NUXMV_OP_RELEASE,  /**< Release temporal operator. */

    NUXMV_OP_HISTORICALLY, /**< Historically temporal operator. */
    NUXMV_OP_ONCE,         /**< Once temporal operator. */
    NUXMV_OP_YESTERDAY,    /**< Yesterday temporal operator.  */
    NUXMV_OP_SINCE,        /**< Since temporal operator. */
    NUXMV_OP_TRIGGERED,    /**< Triggered temporal operator. */

    NUXMV_OP_INDEX_ACCESS, /**< array[index] access operator. */
    NUXMV_OP_ARRAY_READ,   /**< array read operator. */
    NUXMV_OP_ARRAY_WRITE,  /**< array write operator. */

    NUXMV_OP_BIT_SELECTION, /**< word[j:i] bit selection operator. */
    NUXMV_OP_WORD_CONCAT,   /**< Word concatenation (w1 :: w2) operator. */

    NUXMV_OP_CAST_WORD1,         /**< Cast boolean to unsigned word[1]. */
    NUXMV_OP_CAST_BOOL,          /**< Cast int or unsigned word[1] to boolean */
    NUXMV_OP_CAST_TOINT,         /**< Cast boolean word to integer */
    NUXMV_OP_CAST_SIGNED,        /**< Cast unsigned to signed word operator. */
    NUXMV_OP_CAST_UNSIGNED,      /**< Cast signed to unsigned word operator. */
    NUXMV_OP_CAST_SIGNED_WORD,   /**< Cast integer to signed word. */
    NUXMV_OP_CAST_UNSIGNED_WORD, /**< Cast integer to unsigned word. */

    NUXMV_OP_EXTEND, /**< Word extension function (extend(word, n)). */
    NUXMV_OP_RESIZE, /**< Word resize function (resize(word, n)). */

    NUXMV_OP_SET_UNION, /**< Set union (s1 union s2) operator. */
    NUXMV_OP_SET_IN,    /**< Set inclusion check (e in s) operator. */

    NUXMV_OP_IFTHENELSE, /**< Ternary if-then-else operator. */

    NUXMV_OP_UF, /**< Apply a generic symbol to a list of arguments. */

    NUXMV_OP_LAST_ /**< (List terminator.) */
} nuxmv_op_tag;

/**
 * @brief Visiting order
 *
 * @sa
 * - @ref nuxmv_visit_expr()
 */
typedef enum nuxmv_expr_visit_order {
    /** Each node is traversed before its children. */
    NUXMV_EXPR_VISIT_PRE_ORDER,
    /** Each node is traversed after its children. */
    NUXMV_EXPR_VISIT_POST_ORDER
} nuxmv_expr_visit_order;

/**
 * @brief States when visiting an expression
 *
 * User-defined callback functions shall return one of the following code in
 * order to instruct the visiting routine what to do next.
 *
 * @sa
 * - @ref nuxmv_expr_visit_callback
 * - @ref nuxmv_visit_expr()
 */
typedef enum nuxmv_expr_visit_status {
    NUXMV_EXPR_VISIT_PROCESS, /**< Process current node's children. */
    NUXMV_EXPR_VISIT_SKIP,    /**< Skip current node's children. */
    NUXMV_EXPR_VISIT_ABORT    /**< Abort the visiting process. */
} nuxmv_expr_visit_status;

/**
 * @brief Type for user-defined callback functions when visiting an expression
 *
 * This function pointer type defines the signature for callbacks that are
 * invoked when visiting an expression.
 *
 * @param[in] env
 *     Environment of the expression being visited.
 * @param[in] expr
 *     Currently visited expression.
 * @param[in] user_data
 *     Any user-defined context data passed via @ref nuxmv_visit_expr().
 *
 * @sa
 * - @ref nuxmv_visit_expr()
 */
typedef nuxmv_expr_visit_status (*nuxmv_expr_visit_callback)(nuxmv_env env,
                                                             nuxmv_expr expr,
                                                             void *user_data);

/**
 * @brief Module object
 *
 * @sa
 * - @ref nuxmv_create_module()
 * - @ref nuxmv_create_module_from_property()
 */
typedef struct nuxmv_module {
    /** Opaque pointer representing a module. */
    void *repr;
} nuxmv_module;

/**
 * @brief Variable declaration
 *
 * A variable declaration is a pair of @p identifier and @p var_type associating
 * the identifier to the variable type.
 *
 * @sa
 * - @ref NUXMV_MAKE_VAR_DECL()
 * - @ref nuxmv_module_add_state_var()
 * - @ref nuxmv_model_get_state_var()
 */
typedef struct nuxmv_var_decl {
    /** The identifier of the variable. */
    nuxmv_symbol identifier;
    /** The type of the variable. */
    nuxmv_var_type var_type;
} nuxmv_var_decl;

/**
 * @brief Symbol value
 *
 * A symbol value is a pair of @p identifier and @p value associating
 * the symbol identifier to the symbol value.
 *
 * @sa
 * - @ref NUXMV_VALID_TRACE_VALUE()
 * - @ref nuxmv_trace_get_step_state()
 * - @ref nuxmv_trace_get_step_input()
 * - @ref nuxmv_trace_get_step_define()
 * - @ref nuxmv_trace_get_function()
 */
typedef struct nuxmv_trace_value {
    /** The identifier of the symbol. */
    nuxmv_expr identifier;
    /** The value of the symbol. */
    nuxmv_expr value;
} nuxmv_trace_value;

/**
 * @brief Function declaration
 *
 * A function declaration is a pair of @p identifier and @p nuxmv_expr_type
 * associating the identifier to the function type.
 *
 * @sa
 * - @ref NUXMV_MAKE_FUN_DECL()
 * - @ref nuxmv_module_add_function()
 * - @ref nuxmv_module_get_function()
 */
typedef struct nuxmv_fun_decl {
    /** The identifier of the function. */
    nuxmv_symbol identifier;
    /** The type of the function. */
    nuxmv_var_type fun_type;
} nuxmv_fun_decl;

/**
 * @brief Assignment
 *
 * An assignment consists of a pair of expressions: the left- and the right-hand
 * sides of the equal sign.
 *
 * @sa
 * - @ref NUXMV_VALID_ASSIGN()
 * - @ref nuxmv_module_get_init_assign()
 * - @ref nuxmv_module_get_next_assign()
 * - @ref nuxmv_module_get_invar_assign()
 * - @ref nuxmv_model_get_init_assign()
 * - @ref nuxmv_model_get_next_assign()
 * - @ref nuxmv_model_get_invar_assign()
 */
typedef struct nuxmv_assign {
    /** The left-hand side of the assignment. */
    nuxmv_expr lhs;
    /** The right-hand side of the assignment. */
    nuxmv_expr rhs;
} nuxmv_assign;

/**
 * @brief Compassion constraint
 *
 * A compassion constraint consists of a pair of formulas (p, q); if property @p
 * p is true infinitely often in a fair path, then also formula @p q has to be
 * true infinitely often in the fair path.
 *
 * @sa
 * - @ref NUXMV_VALID_COMPASSION()
 * - @ref nuxmv_module_get_compassion()
 * - @ref nuxmv_model_get_compassion()
 */
typedef struct nuxmv_compassion {
    /** The first formula of the compassion constraint. */
    nuxmv_expr p;
    /** The second formula of the compassion constraint. */
    nuxmv_expr q;
} nuxmv_compassion;

/**
 * @brief Define declaration
 *
 * A define declaration is a pair of @p identifier (expression) and @p body
 * associating the expression to the body.
 *
 * @note
 * Heterogeneous defines are not supported. Types of body and identifier must be
 * equal.
 *
 * @sa
 * - @ref NUXMV_VALID_DEFINE_DECL()
 * - @ref nuxmv_module_get_define()
 * - @ref nuxmv_model_get_define()
 */
typedef struct nuxmv_define_decl {
    /** Identifier of the variable declaraion. */
    nuxmv_expr identifier;
    /** Body of the variable declaraion. */
    nuxmv_expr body;
} nuxmv_define_decl;

/**
 * @brief Model formats
 *
 * @sa
 * - @ref nuxmv_create_model_from_string()
 * - @ref nuxmv_serialize_model_to_string()
 */
typedef enum nuxmv_model_format {
    /** Model follows Symbolic Model Verifier format */
    NUXMV_MODEL_FORMAT_SMV,
    /** Model follows Verification Modulo Theories format */
    NUXMV_MODEL_FORMAT_VMT,
    /** Model follows AIG Model Checker format */
    NUXMV_MODEL_FORMAT_AIG
} nuxmv_model_format;

/**
 * @brief Model object
 *
 * @sa
 * - @ref nuxmv_create_model()
 * - @ref nuxmv_create_model_from_string()
 */
typedef struct nuxmv_model {
    /** Opaque pointer representing a model. */
    void *repr;
} nuxmv_model;

/**
 * @brief Property types
 *
 * @sa
 * - @ref nuxmv_make_property()
 * - @ref nuxmv_make_property_from_string()
 */
typedef enum nuxmv_property_type {
    /** Not a valid property. */
    NUXMV_PROPERTY_INVALID = -1,
    /** Property is an invariant. */
    NUXMV_PROPERTY_INVARSPEC,
    /** Generic property with temporal operators. */
    NUXMV_PROPERTY_LTLSPEC
} nuxmv_property_type;

/**
 * @brief Property object
 *
 * @sa
 * - @ref nuxmv_make_property()
 * - @ref nuxmv_make_property_from_string()
 */
typedef struct nuxmv_property {
    /** Opaque pointer representing a property. */
    void *repr;
} nuxmv_property;

/**
 * @brief Result codes
 *
 * These codes are general and their interpretation depends on the checking
 * context.
 *
 * @sa
 * - @ref nuxmv_result_get_code()
 */
typedef enum nuxmv_result_code {
    /** Not a valid result. */
    NUXMV_RESULT_INVALID = -1,
    /** The property checked was false. */
    NUXMV_RESULT_FALSE,
    /** The property checked was true. */
    NUXMV_RESULT_TRUE,
    /** The check result is still not known. */
    NUXMV_RESULT_UNKNOWN
} nuxmv_result_code;

/**
 * @brief Result code object
 *
 * @sa
 * - @ref nuxmv_property_check_satisfiability()
 * - @ref nuxmv_simulation_get_result()
 * - @ref nuxmv_trace_check_property()
 * - @ref nuxmv_model_check_deadlock()
 * - @ref nuxmv_model_check_receptiveness()
 */
typedef struct nuxmv_result {
    /** Opaque pointer representing a result. */
    void *repr;
} nuxmv_result;

/**
 * @brief Trace formats
 *
 * @sa
 * - @ref nuxmv_make_trace_from_string()
 * - @ref nuxmv_serialize_trace_to_string()
 */
typedef enum nuxmv_trace_format {
    /** Trace follows the Extensible Markup Language syntax. */
    NUXMV_TRACE_FORMAT_XML
} nuxmv_trace_format;

/**
 * @brief Trace object
 *
 * @sa
 * - @ref nuxmv_result_get_trace()
 * - @ref nuxmv_make_trace_from_string()
 */
typedef struct nuxmv_trace {
    /** Opaque pointer representing a trace. */
    void *repr;
} nuxmv_trace;

/**
 * @brief Simulation object
 *
 * @sa
 * - @ref nuxmv_create_simulation()
 */
typedef struct nuxmv_simulation {
    /** Opaque pointer representing a simulation. */
    void *repr;
} nuxmv_simulation;

/**
 * @brief Simulation constraint object
 *
 * @sa
 * - @ref NUXMV_MAKE_SIMULATION_CONSTRAINT()
 * - @ref NUXMV_MAKE_INVALID_EXPR()
 * - @ref nuxmv_create_simulation()
 * - @ref nuxmv_extend_simulation()
 */
typedef struct nuxmv_simulation_constraint {
    /**
     * Constraint (simple expression) for the next steps or an invalid
     * expression if no constraint is provided.
     */
    nuxmv_expr simple_constraint;
    /**
     * Constraint (next expression) for the next steps or an invalid
     * expression if no constraint is provided.
     */
    nuxmv_expr trans_constraint;
    /** ??. */
    nuxmv_trace trace;
    /** ??. */
    size_t trace_start;
    /**
     * Specify a formula to simulate or an invalid expression if no formula is
     * provided. This parameter is considered only when creating MathSAT
     * simulations. It is silently ignored otherwise.
     */
    nuxmv_expr ltl_formula;
} nuxmv_simulation_constraint;

/**
 * @brief Type for callback function when processing serialized streams
 *
 * This function pointer type defines the signature for callbacks that are
 * invoked by a serialization routine whenever a chunk of serialized data
 * becomes available. The user can implement this callback to process the
 * data in a stream-like fashion.
 *
 * @param[in] chunk
 *     Pointer to the current chunk of serialized data.
 * @param[in] chunk_size
 *     Size of the data chunk in bytes.
 * @param[in] user_data
 *     Any user-defined context data, passed via serialization functions.
 * @return
 *     `true` to signal to the serialization function to continue processing
 *     subsequent chunks, `false` to instruct it to stop the process.
 *
 * @sa
 * - @ref nuxmv_serialize_model_to_string()
 * - @ref nuxmv_serialize_trace_to_string()
 *
 * @req 03.002
 */
typedef bool (*nuxmv_serialized_chunk_callback)(char *chunk, size_t chunk_size,
                                                void *user_data);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_opt Options
 * @ingroup nuxmv_group_structs
 *
 * @brief Environment options
 */
///@{

/**
 * @brief Helper macro for making an option
 *
 * @param[in] k
 *     Null-terminated string representing the option key.
 * @param[in] v
 *     Null-terminated string representing the option value.
 * @return
 *     A new @ref nuxmv_opt object.
 *
 * @sa
 * - @ref NUXMV_VALID_OPT()
 */
#define NUXMV_MAKE_OPT(k, v) ((nuxmv_opt){.key = k, .value = v})

/**
 * @brief Valid option
 *
 * This macro checks whether @p opt is a valid @ref nuxmv_opt.
 *
 * @param[in] opt
 *     The option to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 *
 * @sa
 * - @ref NUXMV_MAKE_OPT()
 */
#define NUXMV_VALID_OPT(opt) ((opt).key != NULL && (opt).value != NULL)

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_env Environment
 *
 * @brief Functions for working environment
 */
///@{

/**
 * @brief Valid environment
 *
 * This macro checks whether @p env is a valid @ref nuxmv_env.
 *
 * @param[in] env
 *     The environment to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_ENV(env) ((env).repr != NULL)

/**
 * @brief Create a new environment
 *
 * When no longer needed, the environment shall be freed using
 * @ref nuxmv_destroy_env().
 *
 * @return
 *     The created environment. In case of error, @ref NUXMV_VALID_ENV()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_destroy_env()
 * - @ref nuxmv_env_set_options()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 20.001
 */
nuxmv_env nuxmv_create_env(void);

/**
 * @brief Destroy an environment
 *
 * Destroying an environment will deallocate the memory of all the
 * objects created inside it. It is an error to access an object
 * created by an environment which has been destroyed (the precise
 * behaviour is undefined).
 *
 * @param[in] env
 *     The environment to destroy.
 * @return
 *     `NUXMV_SUCCESS` if the environment was destroyed,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_create_env()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 20.001
 */
nuxmv_status_code nuxmv_destroy_env(nuxmv_env env);

/**
 * @brief Get the last error message and clear it
 *
 * @param[in] env
 *     The environment to inspect.
 * @return
 *     A  null-terminated string, empty in case of no error, or NULL in case the
 *     function fails.
 *
 * @note
 * Only last error message is recorded. A new call to this function should
 * discard any previous error message pointer.
 *
 * @sa
 * - @ref nuxmv_create_env()
 *
 * @req 20.003, 90.006.01
 */
const char *nuxmv_env_get_last_error_message(nuxmv_env env);

/**
 * @brief Set a list of options for the environment
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] opts
 *     A list of options to set.
 * @param[in] opt_num
 *     The number of options in the list.
 * @return
 *     `NUXMV_SUCCESS` if options were set, `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_env_get_option()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 09.002
 */
nuxmv_status_code nuxmv_env_set_options(nuxmv_env env, const nuxmv_opt *opts,
                                        size_t opt_num);

/**
 * @brief Get the number of options for the environment
 *
 * @param[in] env
 *     The environment to inspect.
 * @return
 *     The number of options for the environment or `-1` in case of error.
 *
 * @sa
 * - @ref nuxmv_env_get_option()
 *
 * @req 09.002
 */
int nuxmv_env_get_option_num(nuxmv_env env);

/**
 * @brief Get an option of the environment
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] opt_idx
 *     The index of the option counting from 0.
 * @return
 *     The option of the environment. In case of error, @ref NUXMV_VALID_OPT()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_env_get_option_num()
 * - @ref nuxmv_env_set_options()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 09.002
 */
nuxmv_opt nuxmv_env_get_option(nuxmv_env env, int opt_idx);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_expr_type Expression Types
 *
 * @brief Functions for handling Expression Types
 */
///@{

/**
 * @brief Valid expression type
 *
 * This macro checks whether @p type is a valid @ref nuxmv_expr_type.
 *
 * @param[in] expr_type
 *     The expression type to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_EXPR_TYPE(expr_type) ((expr_type).repr != NULL)

/**
 * @brief Create a Boolean type
 *
 * @param[in] env
 *     The environment to modify.
 * @return
 *     The newly created type. In case of error, @ref NUXMV_VALID_EXPR_TYPE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_expr_type_get_tag()
 * - @ref nuxmv_make_simple_var_type()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_make_boolean_type(nuxmv_env env);

/**
 * @brief Create an integer type
 *
 * @param[in] env
 *     The environment to modify.
 * @return
 *     The newly created integer type. In case of error, @ref
 *     NUXMV_VALID_EXPR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_expr_type_get_tag()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_make_integer_type(nuxmv_env env);

/**
 * @brief Create a real type
 *
 * @param[in] env
 *     The environment to modify.
 * @return
 *     The newly created real type. In case of error, @ref
 *     NUXMV_VALID_EXPR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_expr_type_get_tag()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_make_real_type(nuxmv_env env);

/**
 * @brief Create an enumerative type whose variants are symbolic tags
 *
 * @param[in] env
 *     The environment to modify.
 * @return
 *     The newly created enumerative type. In case of error, @ref
 *     NUXMV_VALID_EXPR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_var_type_with_domain()
 * - @ref nuxmv_expr_type_get_tag()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_make_enum_type(nuxmv_env env);

/**
 * @brief Create a set type
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] elem
 *     A type for the elements in the set.
 * @return
 *     The newly created set type. In case of error, @ref
 *     NUXMV_VALID_EXPR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_set_type_get_element()
 * - @ref nuxmv_expr_type_get_tag()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @note
 * This function must be used only with expressions. The usage with with
 * variables is not allowed.
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_make_set_type(nuxmv_env env, nuxmv_expr_type elem);

/**
 * @brief Create a signed word type
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] width
 *     The number of bits for the word.
 * @return
 *     The newly created word type. In case of error, @ref
 *     NUXMV_VALID_EXPR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_word_type_get_width()
 * - @ref nuxmv_expr_type_get_tag()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_make_signed_word_type(nuxmv_env env, size_t width);

/**
 * @brief Create an unsigned word type
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] width
 *     The number of bits for the word.
 * @return
 *     The newly created word type. In case of error, @ref
 *     NUXMV_VALID_EXPR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_word_type_get_width()
 * - @ref nuxmv_expr_type_get_tag()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_make_unsigned_word_type(nuxmv_env env, size_t width);

/**
 * @brief Create an array type
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] idx
 *     A type for the array index.
 * @param[in] elem
 *     A type for the array's elements.
 * @return
 *     The newly created array type. In case of error, @ref
 *     NUXMV_VALID_EXPR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_array_type_get_index()
 * - @ref nuxmv_array_type_get_element()
 * - @ref nuxmv_make_var_type_array()
 * - @ref nuxmv_expr_type_get_tag()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_make_array_type(nuxmv_env env, nuxmv_expr_type idx,
                                      nuxmv_expr_type elem);

/**
 * @brief Create a new (uninterpreted) function type
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] args
 *     A list of function's arguments.
 * @param[in] arg_num
 *     The number of arguments in the list.
 * @param[in] result
 *     The type of the result returned by the function.
 * @return
 *     The newly created function type. In case of error,
 *     @ref NUXMV_VALID_EXPR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_function_type_get_argument()
 * - @ref nuxmv_function_type_get_result()
 * - @ref nuxmv_expr_type_get_tag()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_make_function_type(nuxmv_env env,
                                         const nuxmv_expr_type *args,
                                         size_t arg_num,
                                         nuxmv_expr_type result);

/**
 * @brief Get the tag of a type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The expression type to extract the tag from.
 * @return
 *     The tag of the expression, @ref NUXMV_TYPE_INVALID in case of error.
 *
 * @sa
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type_tag nuxmv_expr_type_get_tag(nuxmv_env env,
                                            nuxmv_expr_type type);

/**
 * @brief Get the ID of a type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The expression type to extract the ID from.
 * @return
 *     The ID of the type, which is a positive integer that is unique
 *     in the given environment. 0 is returned in case of error.
 */
size_t nuxmv_expr_type_get_id(nuxmv_env env, nuxmv_expr_type type);

/**
 * @brief Get the width of a (un)signed word type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The expression type to extract the width from.
 * @return
 *     The width of the (un)signed word or `-1` in case of error.
 *
 * @sa
 * - @ref nuxmv_make_signed_word_type()
 * - @ref nuxmv_make_unsigned_word_type()
 *
 * @req 03.001.03
 */
int nuxmv_word_type_get_width(nuxmv_env env, nuxmv_expr_type type);

/**
 * @brief Get the type of the index of an array type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The array type to extract the index type from.
 * @return
 *     The type of the index. In case of error, @ref NUXMV_VALID_EXPR_TYPE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_array_type()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_array_type_get_index(nuxmv_env env, nuxmv_expr_type type);

/**
 * @brief Get the type of the elements of an array type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The array type to extract the element type from.
 * @return
 *     The type of the elements. In case of error, @ref NUXMV_VALID_EXPR_TYPE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_array_type()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_array_type_get_element(nuxmv_env env,
                                             nuxmv_expr_type type);

/**
 * @brief Get the number of arguments of a function type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The function type to extract the argument type number from.
 * @return
 *     The number of arguments in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the function type be modified, the returned number
 * is no longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_function_type_get_argument()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
int nuxmv_function_type_get_argument_num(nuxmv_env env, nuxmv_expr_type type);

/**
 * @brief Get the *i*-th argument type of a function type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The function type to extract the argument type from.
 * @param[in] arg_idx
 *     The index of the argument counting from 0.
 * @return
 *     The option of the environment. In case of error, @ref
 *     NUXMV_VALID_EXPR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_function_type()
 * - @ref nuxmv_function_type_get_argument_num()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_function_type_get_argument(nuxmv_env env,
                                                 nuxmv_expr_type type,
                                                 int arg_idx);

/**
 * @brief Get the type of the result of a function type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The function type to extract the result type from.
 * @return
 *     The type of result. In case of error, @ref NUXMV_VALID_EXPR_TYPE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_function_type()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_function_type_get_result(nuxmv_env env,
                                               nuxmv_expr_type type);

/**
 * @brief Get the type of the elements of a set type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The set type to extract the element type from.
 * @return
 *     The type of result. In case of error, @ref NUXMV_VALID_EXPR_TYPE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_set_type()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr_type nuxmv_set_type_get_element(nuxmv_env env, nuxmv_expr_type type);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_var_type Variable Types
 *
 * @brief Functions for handling Variable Types
 */
///@{

/**
 * @brief Valid variable type
 *
 * This macro checks whether @p var_type is a valid @ref nuxmv_var_type.
 *
 * @param[in] var_type
 *     The variable type to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_VAR_TYPE(var_type) ((var_type).repr != NULL)

/**
 * @brief Get the variable type corresponding to a type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] type
 *     The expression type to inspect.
 * @return
 *     The simple variable type representing the expression.
 *
 * @sa
 * - @ref nuxmv_make_boolean_type()
 * - @ref nuxmv_make_integer_type()
 * - @ref nuxmv_make_real_type()
 * - @ref nuxmv_make_set_type()
 * - @ref nuxmv_make_signed_word_type()
 * - @ref nuxmv_make_unsigned_word_type()
 * - @ref nuxmv_make_function_type()
 *
 * @req 03.001.03
 */
nuxmv_var_type nuxmv_make_simple_var_type(nuxmv_env env, nuxmv_expr_type type);

/**
 * @brief Get the variable type corresponding to an enumerative
 *
 * It specifies enumerative values for the variable type.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] domain
 *     The list of identifiers that belongs to the domain. All identifiers shall
 *     be of the same type.
 * @param[in] domain_num
 *     The number of values in the list.
 * @return
 *     The variable type representing the enumerative. In case of error, @ref
 *     NUXMV_VALID_VAR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_make_enum_type()
 * - @ref nuxmv_make_real_type()??
 * - @ref nuxmv_make_set_type()??
 * - @ref nuxmv_make_identifier()
 *
 * @req 03.001.03
 */
nuxmv_var_type nuxmv_make_var_type_with_domain(nuxmv_env env,
                                               const nuxmv_expr *domain,
                                               size_t domain_num);

/**
 * @brief Returns the var_type corresponding to the selected bounded int type.
 *
 * It specifies lower and upper bounds for the var_type.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] min
 *     The minimum value in the range, inclusive.
 * @param[in] max
 *     The maximum value in the range, inclusive.
 * @return
 *     The variable type representing the array. In case of error, @ref
 *     NUXMV_VALID_VAR_TYPE() evaluates to `false`.
 *
 * @req 03.001.03
 */
nuxmv_var_type nuxmv_make_var_type_with_integer_range(nuxmv_env env, int min,
                                                      int max);

/**
 * @brief Builds an array var_type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] idx
 *     The variable type for the array index.
 * @param[in] elem
 *     The variable type for the array's elements.
 * @return
 *     The variable type representing the array. In case of error, @ref
 *     NUXMV_VALID_VAR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_array_type()
 *
 * @req ??
 */
nuxmv_var_type nuxmv_make_var_type_array(nuxmv_env env, nuxmv_var_type idx,
                                         nuxmv_var_type elem);

/**
 * @brief Get the expression type corresponding to a variable type.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] var_type
 *     The variable type to inspect.
 * @return
 *     The expression type representing the variable type.
 */
nuxmv_expr_type nuxmv_var_type_get_expr_type(nuxmv_env env,
                                             nuxmv_var_type var_type);

/**
 * @brief Get the tag of a var_type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] var_type
 *     The variable type to extract the tag from.
 * @return
 *     The tag of the var type, @ref NUXMV_VAR_TYPE_INVALID in case of error.
 *
 * @sa
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_var_type_tag nuxmv_var_type_get_tag(nuxmv_env env,
                                          nuxmv_var_type var_type);

/**
 * @brief Get the ID of a var type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] var_type
 *     The var type to extract the ID from.
 * @return
 *     The ID of the type, which is a positive integer that is unique
 *     in the given environment. 0 is returned in case of error.
 */
size_t nuxmv_var_type_get_id(nuxmv_env env, nuxmv_var_type var_type);

/**
 * @brief Get the var type of the index of an array var type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] var_type
 *     The array var type to extract the index type from.
 * @return
 *     The var type of the index. In case of error, @ref NUXMV_VALID_VAR_TYPE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_var_type_array()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_var_type nuxmv_var_type_array_get_index(nuxmv_env env,
                                              nuxmv_var_type var_type);

/**
 * @brief Get the var type of the element of an array var type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] var_type
 *     The array var type to extract the element type from.
 * @return
 *     The var type of the element. In case of error,
 *     @ref NUXMV_VALID_VAR_TYPE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_var_type_array()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_var_type nuxmv_var_type_array_get_element(nuxmv_env env,
                                                nuxmv_var_type var_type);

/**
 * @brief Get the min value an integer range var type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] var_type
 *     The integer range var type to extract the min value from.
 * @return
 *     The min value of the range. In case of error, `INT_MIN` is returned.
 *
 * @sa
 * - @ref nuxmv_make_var_type_with_integer_range()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
int nuxmv_var_type_integer_range_get_min(nuxmv_env env,
                                         nuxmv_var_type var_type);

/**
 * @brief Get the max value an integer range var type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] var_type
 *     The integer range var type to extract the max value from.
 * @return
 *     The max value of the range. In case of error, `INT_MIN` is returned.
 *
 * @sa
 * - @ref nuxmv_make_var_type_with_integer_range()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
int nuxmv_var_type_integer_range_get_max(nuxmv_env env,
                                         nuxmv_var_type var_type);

/**
 * @brief Get the number of elements of a var type with domain
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] var_type
 *     The var type with domain to extract the number of elements from.
 * @return
 *     The number of elements in the var type domain.
 *     In case of error, `-1` is returned.
 *
 * @sa
 * - @ref nuxmv_make_var_type_with_domain()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
int nuxmv_var_type_get_domain_num(nuxmv_env env, nuxmv_var_type var_type);

/**
 * @brief Get the domain element at the given index of a var type with domain
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] var_type
 *     The var type with domain to extract the number of elements from.
 * @param[in] elem_idx
 *     The index of the domain element to retrieve.
 * @return
 *     The domain element at the given index. In case of error,
 *     @ref NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_var_type_with_domain()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.03
 */
nuxmv_expr nuxmv_var_type_get_domain_element(nuxmv_env env,
                                             nuxmv_var_type var_type,
                                             int elem_idx);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_symbol Symbols
 *
 * @brief Functions for handling Symbols
 */
///@{

/**
 * @brief Valid symbol
 *
 * This macro checks whether @p symbol is a valid @ref nuxmv_symbol.
 *
 * @param[in] symbol
 *     The symbol to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_SYMBOL(symbol) ((symbol).repr != NULL)

/**
 * @brief Create a new symbol
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] name
 *     The name of the symbol as a null-terminated string.
 * @return
 *     The newly created symbol. In case of error, @ref NUXMV_VALID_SYMBOL()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_scoped_symbol()
 * - @ref nuxmv_symbol_get_name()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.01
 */
nuxmv_symbol nuxmv_make_symbol(nuxmv_env env, const char *name);

/**
 * @brief Create a new symbol with the given name and context
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] name
 *     The name of the scoped symbol as a null-terminated string.
 * @param[in] scope
 *     A context the symbol belongs to.
 * @return
 *     The newly created symbol. In case of error, @ref NUXMV_VALID_SYMBOL()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_symbol_get_name()
 * - @ref nuxmv_symbol_is_scoped()
 * - @ref nuxmv_symbol_get_scope()
 * - @ref nuxmv_make_symbol()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.01
 */
nuxmv_symbol nuxmv_make_scoped_symbol(nuxmv_env env, const char *name,
                                      nuxmv_symbol scope);

/**
 * @brief Get the ID of a symbol
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] sym
 *     The symbol to extract the ID from.
 * @return
 *     The ID of the symbol, which is a positive integer that is unique
 *     in the given environment. 0 is returned in case of error.
 */
size_t nuxmv_symbol_get_id(nuxmv_env env, nuxmv_symbol sym);

/**
 * @brief Get the name of a symbol
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] symbol
 *     The symbol to inspect.
 * @return
 *     The name as a null-terminated string or `NULL` in case of error.
 *
 * @sa
 * - @ref nuxmv_make_symbol()
 * - @ref nuxmv_make_scoped_symbol()
 *
 * @req 03.001.02
 */
const char *nuxmv_symbol_get_name(nuxmv_env env, nuxmv_symbol symbol);

/**
 * @brief Test whether a symbol is scoped
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] symbol
 *     The symbol to test.
 * @return
 *     `1` when the symbol belongs to a context, `0` if not, `-1` in case of
 *     error.
 *
 * @sa
 * - @ref nuxmv_make_scoped_symbol()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
int nuxmv_symbol_is_scoped(nuxmv_env env, nuxmv_symbol symbol);

/**
 * @brief Get the scope of a symbol
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] symbol
 *     The scoped symbol to inspect.
 * @return
 *     The symbol's context. In case of error, @ref NUXMV_VALID_SYMBOL()
 *     evaluates to `false`.
 *
 * @note
 * Passing a non-scoped symbol results in an error.
 *
 * @sa
 * - @ref nuxmv_make_scoped_symbol()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
nuxmv_symbol nuxmv_symbol_get_scope(nuxmv_env env, nuxmv_symbol symbol);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_expr Expressions
 *
 * @brief Functions for handling Expressions
 */
///@{

/**
 * Make an invalid expression object
 *
 * This macro is useful where a function argument requires an optional
 * expression object.
 *
 * @sa
 * - @ref nuxmv_simulation_constraint()
 */
#define NUXMV_MAKE_INVALID_EXPR() ((nuxmv_expr){.repr = NULL})

/**
 * @brief Valid expression
 *
 * This macro checks whether @p expr is a valid @ref nuxmv_expr.
 *
 * @param[in] expr
 *     The expression to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_EXPR(expr) ((expr).repr != NULL)

/**
 * @brief Create a new identifier for a symbol
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] symbol
 *     A symbol to identify.
 * @param[in] type
 *     The type for the identifier.
 * @return
 *     The newly created identifier. In case of error, @ref NUXMV_VALID_EXPR()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_expr_is_identifier()
 * - @ref nuxmv_expr_get_symbol()
 * - @ref nuxmv_expr_get_type()
 * - @ref nuxmv_make_expr_from_string()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.01
 */
nuxmv_expr nuxmv_make_identifier(nuxmv_env env, nuxmv_symbol symbol,
                                 nuxmv_expr_type type);

/**
 * @brief Create a new value for a symbol
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] val
 *     The value for the symbol.
 * @param[in] type
 *     The type of the value.
 * @return
 *     The newly created value. In case of error, @ref NUXMV_VALID_EXPR()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_expr_is_value()
 * - @ref nuxmv_expr_get_symbol()
 * - @ref nuxmv_expr_get_type()
 * - @ref nuxmv_make_expr_from_string()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.01
 */
nuxmv_expr nuxmv_make_value(nuxmv_env env, nuxmv_symbol val,
                            nuxmv_expr_type type);

/**
 * @brief Create a structured expression for an operator
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] op
 *     The operation computed by the expression.
 * @param[in] args
 *     A list of arguments the operator requires as inputs.
 *     If no list shall be used (for example with operator NUXMV_OP_PI)
 *     it is safe to use NULL or the result of malloc(0),
 *     provided that arg_num=0.
 * @param[in] arg_num
 *     The number of arguments in the list. If no list shall be passed,
 *     use 0 as actual value of arg_num.
 * @return
 *     The newly created structured expression. In case of error,
 *     @ref NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @note
 * If the operation requires one or more parameters, refer to @ref
 * nuxmv_make_parametric_op().
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_expr_is_op()
 * - @ref nuxmv_expr_get_op_tag()
 * - @ref nuxmv_expr_get_argument()
 * - @ref nuxmv_expr_contains_temporal_operators()
 * - @ref nuxmv_visit_expr()
 * - @ref nuxmv_expr_get_type()
 * - @ref nuxmv_make_expr_from_string()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.01
 */
nuxmv_expr nuxmv_make_op(nuxmv_env env, nuxmv_op_tag op, const nuxmv_expr *args,
                         size_t arg_num);

/**
 * @brief Create a structured parametric expression for an operator.
 *
 * This function shall be used when one of the following operations is needed.
 * Each operation takes one expression in @p args and a fixed number of
 * parameters as @p params in the described order:
 * - @ref NUXMV_OP_BIT_SELECTION
 *   1. @p msb (≥ 0): the most significant bit (inclusive) of the selection
 *   2. @p lsb (≤ @p msb): the least significant bit (inclusive) of the
 *      selection
 * - @ref NUXMV_OP_CAST_SIGNED_WORD and @ref NUXMV_OP_CAST_UNSIGNED_WORD
 *   1. @p width (> 0) of the result word expression
 * - @ref NUXMV_OP_EXTEND
 *   1. @p amount (≥ 0) of the extension
 * - @ref NUXMV_OP_RESIZE
 *   1. @p width (> 0) of the result word expression
 *
 * For all other operators, refer to @ref nuxmv_make_op().
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] op
 *     The operation computed by the expression.
 * @param[in] args
 *     A list of arguments the operator requires as inputs.
 * @param[in] arg_num
 *     The number of arguments in the list.
 * @param[in] params
 *     A list of parameters the operator requires as inputs.
 * @param[in] param_num
 *     The number of parameters in the list.
 * @return
 *     The newly created structured expression. In case of error,
 *     @ref NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_expr_is_parametric()
 * - @ref nuxmv_expr_get_parameter()
 * - @ref nuxmv_expr_is_op()
 * - @ref nuxmv_expr_get_op_tag()
 * - @ref nuxmv_expr_get_argument()
 * - @ref nuxmv_expr_contains_temporal_operators()
 * - @ref nuxmv_visit_expr()
 * - @ref nuxmv_expr_get_type()
 * - @ref nuxmv_make_expr_from_string()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.01
 */
nuxmv_expr nuxmv_make_parametric_op(nuxmv_env env, nuxmv_op_tag op,
                                    const nuxmv_expr *args, size_t arg_num,
                                    const int *params, size_t param_num);

/**
 * @brief Create a structured expression for a unary operator
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] op
 *     The operation computed by the expression.
 * @param[in] arg
 *     The argument of the operator.
 * @return
 *     The newly created structured expression. In case of error,
 *     @ref NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_op()
 *
 * @req 03.001.01
 */
nuxmv_expr nuxmv_make_un_op(nuxmv_env env, nuxmv_op_tag op, nuxmv_expr arg);

/**
 * @brief Create a structured expression for a binary operator
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] op
 *     The operation computed by the expression.
 * @param[in] arg1
 *     The first argument of the operator.
 * @param[in] arg2
 *     The second argument of the operator.
 * @return
 *     The newly created structured expression. In case of error,
 *     @ref NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_op()
 *
 * @req 03.001.01
 */
nuxmv_expr nuxmv_make_bin_op(nuxmv_env env, nuxmv_op_tag op, nuxmv_expr arg1,
                             nuxmv_expr arg2);

/**
 * @brief Make an expression from a string
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] data
 *     A null-terminated string containing the expression data.
 * @param[in] scope
 *     A context the expression belongs to, or an invalid module if no context
 *     is required.
 * @return
 *     The newly created expression corresponding to the string. In case of
 *     error, @ref NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref NUXMV_MAKE_INVALID_MODULE()
 * - @ref nuxmv_expr_get_type()
 * - @ref nuxmv_visit_expr()
 * - @ref nuxmv_make_identifier()
 * - @ref nuxmv_make_value()
 * - @ref nuxmv_make_op()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.005
 */
nuxmv_expr nuxmv_make_expr_from_string(nuxmv_env env, const char *data,
                                       nuxmv_module scope);

/**
 * @brief Get the type of an expression
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to inspect.
 * @return
 *     The expression type. In case of error, @ref NUXMV_VALID_EXPR_TYPE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
nuxmv_expr_type nuxmv_expr_get_type(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Get the symbol associated to an identifier
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] identifier
 *     The identifier to inspect.
 * @return
 *     The associated symbol. If no symbol is associated or in case of error,
 *     @ref NUXMV_VALID_SYMBOL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
nuxmv_symbol nuxmv_expr_get_symbol(nuxmv_env env, nuxmv_expr identifier);

/**
 * @brief Get the ID of a type
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to extract the ID from.
 * @return
 *     The ID of the expression, which is a positive integer that is unique
 *     in the given environment. 0 is returned in case of error.
 */
size_t nuxmv_expr_get_id(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Serialize a expr to a string
 *
 * The output is written to the provided buffer. When the serialization process
 * fills up the buffer:
 * - if a callback is not provided, a value equal to or greater than @p
 *   data_size is returned;
 * - if a callback is provided, it is invoked with the user-defined context.
 *
 * The callback is responsible for handling the data chunk (e.g., copying it
 * elsewhere). If the callback returns `false`, the process is aborted and the
 * function returns the number of bytes written up to that point.
 *
 * When the serialization process is completed successfully, the output buffer
 * contains a null-terminated string and the callback is called, if any.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expr to serialize.
 * @param[in] callback
 *     Optional callback function invoked whenever the buffer is full or the
 *     serialization process is completed.
 * @param[in] user_data
 *     User-defined context passed to the callback.
 * @param[out] data
 *     The buffer where the serialized expr will be stored.
 * @param[in] data_size
 *     The size of the data buffer.
 * @return
 *     - The total number of bytes written, including the terminating null byte,
 *       upon successful completion;
 *     - a value equal to or greater than @p data_size, if no callback is
 *       provided and the serialized expression was truncated;
 *     - the accumulated number of bytes for all successful calls of the
 *       @p callback, if the @p callback eventually requests to stop;
 *     - `-1` in case of error.
 *
 * @sa
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.002
 */
int nuxmv_serialize_expr_to_string(nuxmv_env env, nuxmv_expr expr,
                                   nuxmv_serialized_chunk_callback callback,
                                   void *user_data, char *data,
                                   size_t data_size);

/**
 * @brief Test whether an expression contains temporal operators
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to inspect.
 * @return
 *     `1` when the expression contains at least one temporal operator, `0` if
 *     not, `-1` in case of error.
 *
 * @sa
 * - @ref nuxmv_make_op()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
int nuxmv_expr_contains_temporal_operators(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Test whether an expression corresponds to an identifier
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to inspect.
 * @return
 *     `1` when the expression is an identifier for a symbol, `0` if not, `-1`
 *     in case of error.
 *
 * @sa
 * - @ref nuxmv_make_identifier()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
int nuxmv_expr_is_identifier(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Test whether an expression corresponds to a value
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to inspect.
 * @return
 *     `1` when the expression is a value for a symbol, `0` if not, `-1` in case
 *     of error.
 *
 * @sa
 * - @ref nuxmv_make_value()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
int nuxmv_expr_is_value(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Test whether an expression corresponds to an operator
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to inspect.
 * @return
 *     `1` when the expression is strctured, `0` if not, `-1` in case of error.
 *
 * @sa
 * - @ref nuxmv_make_op()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
int nuxmv_expr_is_op(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Get the tag of an operator
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The structured expression to inspect.
 * @return
 *     The tag identifying the operator. In case of error, @ref NUXMV_OP_INVALID
 *     is returned.
 *
 * @sa
 * - @ref nuxmv_make_op()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.04
 */
nuxmv_op_tag nuxmv_expr_get_op_tag(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Get the number of arguments in an expression
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to extract the argument number from.
 * @return
 *     The number of arguments in the expression or `-1` in case of error.
 *
 * @note
 * Should the environment or the expression be modified, the returned number is
 * no longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_expr_get_argument()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
int nuxmv_expr_get_argument_num(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Get the *i*-th argument of a structured expression
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The structured expression to inspect.
 * @param[in] arg_idx
 *     The index of the argument counting from 0.
 * @return
 *     The argument of the structured expression. In case of error, @ref
 *     NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_op()
 * - @ref nuxmv_expr_get_argument_num()
 * - @ref nuxmv_expr_get_parameter()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.02
 */
nuxmv_expr nuxmv_expr_get_argument(nuxmv_env env, nuxmv_expr expr, int arg_idx);

/**
 * @brief Test whether an expression is parametric
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to inspect.
 * @return
 *     `1` when the expression is strctured and parametric, `0` if not, `-1` in
 *     case of error.
 *
 * @sa
 * - @ref nuxmv_make_parametric_op()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.01
 */
int nuxmv_expr_is_parametric(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Get the number of parameters in a parametric expression
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to extract the parameter number from.
 * @return
 *     The number of parameters in the expression or `-1` in case of error.
 *
 * @note
 * Should the environment or the expression be modified, the returned number is
 * no longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_expr_get_parameter()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.01
 */
int nuxmv_expr_get_parameter_num(nuxmv_env env, nuxmv_expr expr);

/**
 * @brief Get the *i*-th parameter value of a structured parametric expression
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The structured parametric expression to inspect.
 * @param[in] param_idx
 *     The index of the parameter counting from 0.
 * @return
 *     The parameter value of the structured parametric expression or `-1` in
 *     case of error.
 *
 * @sa
 * - @ref nuxmv_make_parametric_op()
 * - @ref nuxmv_expr_get_parameter_num()
 * - @ref nuxmv_expr_get_argument()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001.01
 */
int nuxmv_expr_get_parameter(nuxmv_env env, nuxmv_expr expr, int param_idx);

/**
 * @brief Visit an expression
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to visit.
 * @param[in] callback
 *     A user-defined function which is called for each node that composes the
 *     given expression.
 * @param[in] order
 *     The order which the expression's nodes are traversed.
 * @param[in] user_data
 *     Any user-defined context data passed to the callback function as-is.
 * @return
 *     `1` if expression was visited completely, `0` if not, `-1` in case of
 *     error.
 *
 * @sa
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.001
 */
int nuxmv_visit_expr(nuxmv_env env, nuxmv_expr expr,
                     nuxmv_expr_visit_callback callback,
                     nuxmv_expr_visit_order order, void *user_data);

/**
 * @brief Simplify an expression
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] expr
 *     The expression to simplify.
 * @return
 *     A new simplified expression. In case of error, @ref NUXMV_VALID_EXPR()
 *     evaluates to `false`.
 *
 * TODO: useful?? we need to understand if when building nuxmv expressions we
 *       are implicitly performing some simplifications
 *       (e.g. a conjunction containing a TRUE is stored as TRUE)
 *       See also issue #16.
 *
 * @req 03.001
 */
nuxmv_expr nuxmv_simplify_expr(nuxmv_env env, nuxmv_expr expr);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_module Modules
 *
 * @brief Functions for handling Modules
 *
 * This section lists all the functions related to module handling. They are
 * grouped into two main categories:
 * - functions that @ref nuxmv_group_module_add "add" objectes to a module, and
 * - functions that @ref nuxmv_group_module_get "get" objects from it.
 */
///@{

/**
 * Make an invalid module object
 *
 * This macro is useful where a function argument requires an optional module
 * object.
 *
 * @sa
 * - @ref nuxmv_make_expr_from_string()
 */
#define NUXMV_MAKE_INVALID_MODULE() ((nuxmv_module){.repr = NULL})

/**
 * @brief Valid module
 *
 * This macro checks whether @p module is a valid @ref nuxmv_module.
 *
 * @param[in] module
 *     The module to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_MODULE(module) ((module).repr != NULL)

/**
 * @brief Create a new module
 *
 * The created module belongs to the environment. It can be freed using
 * @ref nuxmv_destroy_module(), otherwise it is automatically deleted by
 * using @ref nuxmv_destroy_env().
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] name
 *     The name of the module as a null-terminated string.
 * @return
 *     The newly created module. In case of error, @ref NUXMV_VALID_MODULE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_create_module_from_property()
 * - @ref nuxmv_copy_module()
 * - @ref nuxmv_destroy_module()
 * - @ref nuxmv_module_add_property()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_module nuxmv_create_module(nuxmv_env env, const char *name);

/**
 * @brief Create a new module out of a property
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] name
 *     The name of the module as a null-terminated string.
 * @param[in] property
 *     The property to inspect.
 * @param[in] opts
 *     A list of options for creating the module.
 *     If no list shall be used it is safe to use NULL or the
 *     result of malloc(0), provided that opt_num=0.
 * @param[in] opt_num
 *     The number of options in the list. If no list shall be passed,
 *     use 0 as actual value of opt_num.
 * @return
 *     The newly created module. In case of error, @ref NUXMV_VALID_MODULE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_create_module()
 *
 * @req 02.007
 *
 * @unimplemented
 */
nuxmv_module nuxmv_create_module_from_property(nuxmv_env env, const char *name,
                                               nuxmv_property property,
                                               const nuxmv_opt *opts,
                                               size_t opt_num);

/**
 * @brief Destroy a module
 *
 * With this function, the user notifies the environment that the
 * selected module is no more needed. Note that destroying a module
 * has no effect on its submodules. Coversely, destroying a module
 * that was added as a submodule will leave a dangling reference,
 * leading to an error (undefined behaviour) if such submodule is ever
 * accessed. It is therefore recommended to not destroy modules
 * explicitly (and rely on @ref nuxmv_destroy_env() instead) unless
 * the user is sure that no dangling references are left.
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     A module to destroy.
 * @return
 *     `NUXMV_SUCCESS` if the module was destroyed,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_create_module()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009
 */
nuxmv_status_code nuxmv_destroy_module(nuxmv_env env, nuxmv_module module);

/**
 * @brief Copy a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     A module to copy from.
 * @param[in] name
 *     The name of the module as a null-terminated string.
 * @return
 *     The newly copied module. In case of error, @ref NUXMV_VALID_MODULE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_create_module()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009
 */
nuxmv_module nuxmv_copy_module(nuxmv_env env, nuxmv_module module,
                               const char *name);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_module_add Module Adders
 * @ingroup nuxmv_group_module
 *
 * @brief Functions for adding objects to a Module
 */
///@{

/**
 * @brief Helper macro for making variable declarations
 *
 * @param[in] identifier_
 *     A @ref nuxmv_symbol as the identifier of the variable.
 * @param[in] var_type_
 *     A @ref nuxmv_var_type as the type of the variable.
 * @return
 *     A new @ref nuxmv_var_decl object.
 *
 * @sa
 * - @ref NUXMV_VALID_VAR_DECL()
 */
#define NUXMV_MAKE_VAR_DECL(identifier_, var_type_)                            \
    ((nuxmv_var_decl){.identifier = identifier_, .var_type = var_type_})

/**
 * @brief Valid variable declaration
 *
 * This macro checks whether @p var_decl is a valid @ref nuxmv_var_decl.
 *
 * @param[in] var_decl_
 *     The variable declaration to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 *
 * @sa
 * - @ref NUXMV_MAKE_VAR_DECL()
 * - @ref nuxmv_module_get_state_var()
 * - @ref nuxmv_module_get_input_var()
 * - @ref nuxmv_module_get_frozen_var()
 */
#define NUXMV_VALID_VAR_DECL(var_decl_)                                        \
    (NUXMV_VALID_SYMBOL((var_decl_).identifier) &&                             \
     NUXMV_VALID_VAR_TYPE((var_decl_).var_type))

/**
 * @brief Helper macro for making function declarations
 *
 * @param[in] identifier_
 *     A @ref nuxmv_symbol as the identifier of the function.
 * @param[in] fun_type_
 *     A @ref nuxmv_expr_type as the type of the function.
 * @return
 *     A new @ref nuxmv_fun_decl object.
 *
 */
#define NUXMV_MAKE_FUN_DECL(identifier_, fun_type_)                            \
    ((nuxmv_fun_decl){.identifier = identifier_, .fun_type = fun_type_})

/**
 * @brief Valid function declaration
 *
 * This macro checks whether @p fun_decl is a valid @ref nuxmv_fun_decl.
 *
 * @param[in] fun_decl_
 *     The function declaration to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 *
 * @sa
 * - @ref NUXMV_MAKE_FUN_DECL()
 * - @ref nuxmv_module_get_function()
 * - @ref nuxmv_model_get_function()
 */
#define NUXMV_VALID_FUN_DECL(fun_decl_)                                        \
    (NUXMV_VALID_SYMBOL((fun_decl_).identifier) &&                             \
     NUXMV_VALID_VAR_TYPE((fun_decl_).fun_type))

/**
 * @brief Helper macro for making an assignment
 *
 * @param[in] lhs_
 *     A @ref nuxmv_expr as the left-hand side of the assignment.
 * @param[in] rhs_
 *     A @ref nuxmv_expr as the right-hand side of the assignment.
 * @return
 *     A new @ref nuxmv_assign object.
 *
 * @sa
 * - @ref NUXMV_VALID_ASSIGN()
 */
#define NUXMV_MAKE_ASSIGN(lhs_, rhs_) ((nuxmv_assign){.lhs = lhs_, .rhs = rhs_})

/**
 * @brief Valid assignment
 *
 * This macro checks whether @p assign is a valid @ref nuxmv_assign.
 *
 * @param[in] assign_
 *     The assignment to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 *
 * @sa
 * - @ref NUXMV_MAKE_ASSIGN()
 * - @ref nuxmv_module_get_init_assign()
 * - @ref nuxmv_module_get_next_assign()
 * - @ref nuxmv_module_get_invar_assign()
 * - @ref nuxmv_model_get_init_assign()
 * - @ref nuxmv_model_get_next_assign()
 * - @ref nuxmv_model_get_invar_assign()
 */
#define NUXMV_VALID_ASSIGN(assign_)                                            \
    (NUXMV_VALID_EXPR((assign_).lhs) && NUXMV_VALID_EXPR((assign_).rhs))

/**
 * @brief Helper macro for making compassions
 *
 * @param[in] p_
 *     A @ref nuxmv_expr as the first formula of the compassion constraint.
 * @param[in] q_
 *     A @ref nuxmv_expr as the second formula of the compassion constraint.
 * @return
 *     A new @ref nuxmv_compassion object.
 *
 * @sa
 * - @ref NUXMV_VALID_COMPASSION()
 */
#define NUXMV_MAKE_COMPASSION(p_, q_) ((nuxmv_compassion){.p = p_, .q = q_})

/**
 * @brief Valid compassion constraint
 *
 * This macro checks whether @p comp is a valid @ref nuxmv_compassion.
 *
 * @param[in] comp_
 *     The compassion constraint to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 *
 * @sa
 * - @ref NUXMV_MAKE_COMPASSION()
 * - @ref nuxmv_module_get_compassion()
 */
#define NUXMV_VALID_COMPASSION(comp_)                                          \
    (NUXMV_VALID_EXPR((comp_).p) && NUXMV_VALID_EXPR((comp_).q))

/**
 * @brief Helper macro for making define declarations
 *
 * @param[in] identifier_
 *     A @ref nuxmv_expr as the identifier of the define.
 * @param[in] body_
 *     A @ref nuxmv_expr as the type of the define.
 * @return
 *     A new @ref nuxmv_define_decl object.
 *
 * @sa
 * - @ref NUXMV_VALID_DEFINE_DECL()
 * - @ref nuxmv_module_add_define()
 */
#define NUXMV_MAKE_DEFINE_DECL(identifier_, body_)                             \
    ((nuxmv_define_decl){.identifier = identifier_, .body = body_})

/**
 * @brief Valid define declaration
 *
 * This macro checks whether @p define_decl is a valid @ref nuxmv_define_decl.
 *
 * @param[in] define_decl_
 *     The define declaration to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 *
 * @sa
 * - @ref NUXMV_MAKE_DEFINE_DECL()
 * - @ref nuxmv_model_get_define()
 * - @ref nuxmv_module_get_define()
 */
#define NUXMV_VALID_DEFINE_DECL(define_decl_)                                  \
    (NUXMV_VALID_EXPR((define_decl_).identifier) &&                            \
     NUXMV_VALID_EXPR((define_decl_).body))

/**
 * @brief Add parameters to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to add parameters to.
 * @param[in] params
 *     A list of parameters to add.
 * @param[in] param_num
 *     The number of parameters in the list.
 * @return
 *     `NUXMV_SUCCESS` when parameters were added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_module_get_param()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_params(nuxmv_env env, nuxmv_module module,
                                          const nuxmv_expr *params,
                                          size_t param_num);

/**
 * @brief Add a state variable to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to add a state variable to.
 * @param[in] var
 *     A unique state variable to add.
 * @return
 *     `NUXMV_SUCCESS` when the state variable was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref NUXMV_MAKE_VAR_DECL()
 * - @ref nuxmv_module_get_state_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_state_var(nuxmv_env env, nuxmv_module module,
                                             nuxmv_var_decl var);

/**
 * @brief Add an input variable to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to add an input variable to.
 * @param[in] var
 *     A unique input variable to add.
 * @return
 *     `NUXMV_SUCCESS` when the input variable was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref NUXMV_MAKE_VAR_DECL()
 * - @ref nuxmv_module_get_input_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_input_var(nuxmv_env env, nuxmv_module module,
                                             nuxmv_var_decl var);

/**
 * @brief Adds a frozen variable to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to add a frozen variable to.
 * @param[in] var
 *     A unique frozen variable to add.
 * @return
 *     `NUXMV_SUCCESS` when the frozen variable was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref NUXMV_MAKE_VAR_DECL()
 * - @ref nuxmv_module_get_frozen_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_frozen_var(nuxmv_env env,
                                              nuxmv_module module,
                                              nuxmv_var_decl var);

/**
 * @brief Add an uninterpreted function declaration to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to add the uninterpreted function declaration to.
 * @param[in] fun_decl
 *     An uninterpreted function declaration to add.
 * @return
 *     `NUXMV_SUCCESS` when the uninterpreted function declaration was added,
 *     `NUXMV_FAILURE` in case of error.
 * @sa
 * - @ref NUXMV_MAKE_FUN_DECL()
 * - @ref nuxmv_module_get_function()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_function(nuxmv_env env, nuxmv_module module,
                                            nuxmv_fun_decl fun_decl);

/**
 * @brief Add an initial constraint to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] init
 *     An initial constraint to add.
 * @return
 *     `NUXMV_SUCCESS` if the initial constraint was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_module_get_init()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_init(nuxmv_env env, nuxmv_module module,
                                        nuxmv_expr init);

/**
 * @brief Add a transition constraint to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] trans
 *     A transition constraint to add.
 * @return
 *     `NUXMV_SUCCESS` if the transition constraint was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_module_get_trans()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_trans(nuxmv_env env, nuxmv_module module,
                                         nuxmv_expr trans);

/**
 * @brief Add an invariant constraint to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] invar
 *     An invariant constraint to add.
 * @return
 *     `NUXMV_SUCCESS` if the invariant constraint was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_module_get_invar()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_invar(nuxmv_env env, nuxmv_module module,
                                         nuxmv_expr invar);

/**
 * @brief Add a justice constraint to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] justice
 *     A justice constraint to add.
 * @return
 *     `NUXMV_SUCCESS` if the justice constraint was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_module_get_justice()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_justice(nuxmv_env env, nuxmv_module module,
                                           nuxmv_expr justice);

/**
 * @brief Add a compassion constraint to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] comp
 *     A compassion constraint.
 * @return
 *     `NUXMV_SUCCESS` if the compassion assignment was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref NUXMV_MAKE_COMPASSION()
 * - @ref nuxmv_module_get_compassion()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_compassion(nuxmv_env env,
                                              nuxmv_module module,
                                              nuxmv_compassion comp);

/**
 * @brief Add a define declaration to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] decl
 *     A unique define declaration to add.
 * @return
 *     `NUXMV_SUCCESS` if the define declaration was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref NUXMV_MAKE_DEFINE_DECL()
 * - @ref nuxmv_module_get_define()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_define(nuxmv_env env, nuxmv_module module,
                                          nuxmv_define_decl decl);

/**
 * @brief Add an initial assignment to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] assign
 *     An assignment to add.
 * @return
 *     `NUXMV_SUCCESS` if the initial assignment was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_module_get_init_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_init_assign(nuxmv_env env,
                                               nuxmv_module module,
                                               nuxmv_assign assign);

/**
 * @brief Add a next assignment to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] assign
 *     An assignment to add.
 * @return
 *     `NUXMV_SUCCESS` if the next assignment was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_module_get_next_assign()
 * - @ref nuxmv_env_get_last_error_message()
 */
nuxmv_status_code nuxmv_module_add_next_assign(nuxmv_env env,
                                               nuxmv_module module,
                                               nuxmv_assign assign);

/**
 * @brief Add an invariant assignment to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] assign
 *     An assignment to add.
 * @return
 *     `NUXMV_SUCCESS` if the invariant assignment was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_module_get_invar_assign()
 * - @ref nuxmv_env_get_last_error_message()
 */
nuxmv_status_code nuxmv_module_add_invar_assign(nuxmv_env env,
                                                nuxmv_module module,
                                                nuxmv_assign assign);

/**
 * @brief Add a property to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] property
 *     A property to add to the module.
 * @return
 *     `NUXMV_SUCCESS` if the invariant assignment was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_make_property()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.008
 */
nuxmv_status_code nuxmv_module_add_property(nuxmv_env env, nuxmv_module module,
                                            nuxmv_property property);

/**
 * @brief Add a submodule to a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] name
 *     An unique name for the submodule instantiation as a null-terminated
 *     string.
 * @param[in] sub
 *     The submodule to add. The submodule must not be destroyed if
 *     the module is still in use.
 * @param[in] params
 *     A list of parameters for the submodule instantiation.
 *     If no list shall be used it is safe to use NULL or the
 *     result of malloc(0), provided that param_num=0.
 * @param[in] param_num
 *     The number of parameters in the list. If no list shall be passed,
 *     use 0 as actual value of param_num.
 * @return
 *     `NUXMV_SUCCESS` if the invariant assignment was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_module_get_submodule_num()
 * - @ref nuxmv_module_get_submodule_name()
 * - @ref nuxmv_module_get_submodule()
 * - @ref nuxmv_module_get_submodule_param()
 * - @ref nuxmv_env_get_last_error_message()
 * - @ref nuxmv_destroy_module()
 *
 * @req 03.009.01
 */
nuxmv_status_code nuxmv_module_add_submodule(nuxmv_env env, nuxmv_module module,
                                             const char *name, nuxmv_module sub,
                                             const nuxmv_expr *params,
                                             size_t param_num);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_module_get Module Getters
 * @ingroup nuxmv_group_module
 *
 * @brief Functions for getting objects from a Module
 */
///@{

/**
 * @brief Get the name of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @return
 *     The name of the module, or NULL in case of error.
 *
 * @sa
 * - @ref nuxmv_env_get_last_error_message()
 *
 */
const char *nuxmv_module_get_name(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the number of parameters of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @return
 *     The number of parameters of the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned list is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_param()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_param_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th parameter of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] param_idx
 *     The index of the parameter counting from 0.
 * @return
 *     The parameter of the module. In case of error, @ref NUXMV_VALID_EXPR()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_params()
 * - @ref nuxmv_module_get_param_num()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_expr nuxmv_module_get_param(nuxmv_env env, nuxmv_module module,
                                  int param_idx);

/**
 * @brief Get the number of state variables in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the state variable number from.
 * @return
 *     The number of state variables in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_state_var()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_state_var_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th state variable of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] var_idx
 *     The index of the state variable counting from 0.
 * @return
 *     The state variable of the module. In case of error, @ref
 *     NUXMV_VALID_VAR_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_state_var()
 * - @ref nuxmv_module_get_state_var_num()
 * - @ref nuxmv_model_get_state_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_var_decl nuxmv_module_get_state_var(nuxmv_env env, nuxmv_module module,
                                          int var_idx);

/**
 * @brief Get the number of input variables in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the input variable number from.
 * @return
 *     The number of input variables in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_input_var()
 *
 * @req ??
 */
int nuxmv_module_get_input_var_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th input variable of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] var_idx
 *     The index of the input variable counting from 0.
 * @return
 *     The input variable of the module. In case of error, @ref
 *     NUXMV_VALID_VAR_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_input_var()
 * - @ref nuxmv_module_get_input_var_num()
 * - @ref nuxmv_model_get_input_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_var_decl nuxmv_module_get_input_var(nuxmv_env env, nuxmv_module module,
                                          int var_idx);

/**
 * @brief Get the number of frozen variables in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the frozen variable number from.
 * @return
 *     The number of frozen variables in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_frozen_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_frozen_var_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th frozen variable of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] var_idx
 *     The index of the frozen variable counting from 0.
 * @return
 *     The frozen variable of the module. In case of error, @ref
 *     NUXMV_VALID_VAR_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_frozen_var()
 * - @ref nuxmv_module_get_frozen_var_num()
 * - @ref nuxmv_model_get_frozen_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_var_decl nuxmv_module_get_frozen_var(nuxmv_env env, nuxmv_module module,
                                           int var_idx);

/**
 * @brief Get the number of uninterpreted function declarations in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the uninterpreted function declaration number from.
 * @return
 *     The number of uninterpreted function declarations in the module or `-1`
 *     in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_function()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_function_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th uninterpreted function declaration of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] fun_idx
 *     The index of the uninterpreted function declaration counting from 0.
 * @return
 *     The uninterpreted function declaration of the module. In case of error,
 * @ref NUXMV_VALID_FUN_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_function()
 * - @ref nuxmv_module_get_function_num
 * - @ref nuxmv_model_get_function()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_fun_decl nuxmv_module_get_function(nuxmv_env env, nuxmv_module module,
                                         int fun_idx);

/**
 * @brief Get the number of initial constraints in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the initial constraint number from.
 * @return
 *     The number of initial constraints in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_init()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_init_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th initial constraint of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] init_idx
 *     The index of the initial constraint counting from 0.
 * @return
 *     The initial constraint of the module. In case of error, @ref
 *     NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_init()
 * - @ref nuxmv_module_get_init_num()
 * - @ref nuxmv_module_get_init_assign()
 * - @ref nuxmv_model_get_init()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_expr nuxmv_module_get_init(nuxmv_env env, nuxmv_module module,
                                 int init_idx);

/**
 * @brief Get the number of transition constraints in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the transition constraint number from.
 * @return
 *     The number of transition constraints in the module or `-1` in case of
 *     error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_trans()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_trans_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th transition constraint of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] trans_idx
 *     The index of the transition constraint counting from 0.
 * @return
 *     The transition constraint of the module. In case of error, @ref
 *     NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_trans()
 * - @ref nuxmv_module_get_trans_num()
 * - @ref nuxmv_model_get_trans()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_expr nuxmv_module_get_trans(nuxmv_env env, nuxmv_module module,
                                  int trans_idx);

/**
 * @brief Get the number of invariant constraints in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the invariant constraint number from.
 * @return
 *     The number of invariant constraints in the module or `-1` in case of
 *     error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_invar()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_invar_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th invariant constraint of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] invar_idx
 *     The index of the invariant constraint counting from 0.
 * @return
 *     The invariant constraint of the module. In case of error, @ref
 *     NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_invar()
 * - @ref nuxmv_module_get_invar_num()
 * - @ref nuxmv_module_get_invar_assign()
 * - @ref nuxmv_model_get_invar()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_expr nuxmv_module_get_invar(nuxmv_env env, nuxmv_module module,
                                  int invar_idx);

/**
 * @brief Get the number of justice constraints in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the justice constraint number from.
 * @return
 *     The number of justice constraints in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_justice()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_justice_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th justice constraint of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] just_idx
 *     The index of the justice constraint counting from 0.
 * @return
 *     The justice constraint of the module. In case of error, @ref
 *     NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_justice()
 * - @ref nuxmv_module_get_justice_num()
 * - @ref nuxmv_model_get_justice()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_expr nuxmv_module_get_justice(nuxmv_env env, nuxmv_module module,
                                    int just_idx);

/**
 * @brief Get the number of compassions in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the compassion number from.
 * @return
 *     The number of compassions in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_compassion()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_compassion_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th compassion of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] comp_idx
 *     The index of the compassion counting from 0.
 * @return
 *     The compassion of the module. In case of error, @ref
 *     NUXMV_VALID_COMPASSION() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_compassion()
 * - @ref nuxmv_module_get_compassion_num()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_compassion nuxmv_module_get_compassion(nuxmv_env env, nuxmv_module module,
                                             int comp_idx);

/**
 * @brief Get the number of define declarations in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the define declaration number from.
 * @return
 *     The number of define declarations in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_define()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_define_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th define declaration of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] def_idx
 *     The index of the define declaration counting from 0.
 * @return
 *     The define declaration of the module. In case of error, @ref
 *     NUXMV_VALID_DEFINE_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_define()
 * - @ref nuxmv_module_get_define_num()
 * - @ref nuxmv_model_get_define()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_define_decl nuxmv_module_get_define(nuxmv_env env, nuxmv_module module,
                                          int def_idx);

/**
 * @brief Get the number of initial assignments in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the initial assignment number from.
 * @return
 *     The number of initial assignments in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_init_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_init_assign_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th initial assignment of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] assign_idx
 *     The index of the initial assignment counting from 0.
 * @return
 *     The initial assignment of the module. In case of error, @ref
 *     NUXMV_VALID_ASSIGN() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_init_assign()
 * - @ref nuxmv_module_get_init_assign_num()
 * - @ref nuxmv_model_get_init_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_assign nuxmv_module_get_init_assign(nuxmv_env env, nuxmv_module module,
                                          int assign_idx);

/**
 * @brief Get the number of next assignments in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the next assignment number from.
 * @return
 *     The number of next assignments in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_next_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req ??
 */
int nuxmv_module_get_next_assign_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th next assignment of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] assign_idx
 *     The index of the next assignment counting from 0.
 * @return
 *     The next assignment of the module. In case of error, @ref
 *     NUXMV_VALID_ASSIGN() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_next_assign()
 * - @ref nuxmv_module_get_next_assign_num()
 * - @ref nuxmv_model_get_next_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req ??
 */
nuxmv_assign nuxmv_module_get_next_assign(nuxmv_env env, nuxmv_module module,
                                          int assign_idx);

/**
 * @brief Get the number of invariant assignments in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the invariant assignment number from.
 * @return
 *     The number of invariant assignments in the module or `-1` in case of
 *     error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_invar_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req ??
 */
int nuxmv_module_get_invar_assign_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th invariant assignment of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] assign_idx
 *     The index of the invariant assignment counting from 0.
 * @return
 *     The invariant assignment of the module. In case of error, @ref
 *     NUXMV_VALID_ASSIGN() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_invar_assign()
 * - @ref nuxmv_module_get_invar_assign_num()
 * - @ref nuxmv_model_get_invar_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req ??
 */
nuxmv_assign nuxmv_module_get_invar_assign(nuxmv_env env, nuxmv_module module,
                                           int assign_idx);

/**
 * @brief Get the number of properties in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to extract the property number from.
 * @return
 *     The number of properties in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_property()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.008
 */
int nuxmv_module_get_property_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the *i*-th property of a module
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to modify.
 * @param[in] prop_idx
 *     The index of the property counting from 0.
 * @return
 *     The property of the module. In case of error, @ref NUXMV_VALID_PROPERTY()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_property()
 * - @ref nuxmv_module_get_property_num()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.008
 */
nuxmv_property nuxmv_module_get_property(nuxmv_env env, nuxmv_module module,
                                         int prop_idx);

/**
 * @brief Get the number of submodules in a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @return
 *     The number of submodules in the module or `-1` in case of error.
 *
 * @note
 * Should the environment or the module be modified, the returned list is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_submodule()
 * - @ref nuxmv_module_get_submodule_name()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_submodule_num(nuxmv_env env, nuxmv_module module);

/**
 * @brief Get the name of the *i*-th submodule of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] sub_idx
 *     The index of the submodule counting from 0.
 * @return
 *     The name of the *i*-th submodule as a null-terminated string or `NULL` in
 *     case of error.
 *
 * @sa
 * - @ref nuxmv_module_add_submodule()
 * - @ref nuxmv_module_get_submodule_num()
 * - @ref nuxmv_module_get_submodule()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
const char *nuxmv_module_get_submodule_name(nuxmv_env env, nuxmv_module module,
                                            int sub_idx);

/**
 * @brief Get the *i*-th submodule of a module
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to inspect.
 * @param[in] sub_idx
 *     The index of the submodule counting from 0.
 * @return
 *     The *i*-th submodule. In case of error, @ref NUXMV_VALID_MODEL()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_submodule()
 * - @ref nuxmv_module_get_submodule_num()
 * - @ref nuxmv_module_get_submodule_name()
 * - @ref nuxmv_module_get_submodule_param()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_module nuxmv_module_get_submodule(nuxmv_env env, nuxmv_module module,
                                        int sub_idx);

/**
 * @brief Get the number of parameters in a submodule
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The parent module to inspect.
 * @param[in] sub_idx
 *     The submodule to extract the parameter number from.
 * @return
 *     The number of parameters in the submodule or `-1` in case of error.
 *
 * @note
 * Should the environment or the submodule be modified, the returned number is
 * no longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_module_get_submodule_num()
 * - @ref nuxmv_module_get_submodule_param()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
int nuxmv_module_get_submodule_param_num(nuxmv_env env, nuxmv_module module,
                                         int sub_idx);

/**
 * @brief Get the *i*-th parameter of a submodule
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The parent module to inspect.
 * @param[in] sub_idx
 *     The submodule to extract the parameter number from.
 * @param[in] param_idx
 *     The index of the parameter counting from 0.
 * @return
 *     The parameter of the submodule. In case of error, @ref NUXMV_VALID_EXPR()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_module_add_submodule()
 * - @ref nuxmv_module_get_submodule_num()
 * - @ref nuxmv_module_get_submodule_param_num()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.02
 */
nuxmv_expr nuxmv_module_get_submodule_param(nuxmv_env env, nuxmv_module module,
                                            int sub_idx, int param_idx);

/**
 * @brief Serialize a module to a string in SMV format
 *
 * This function converts the given module into a string representation using
 * the SMV format.
 *
 * The output is written to the provided buffer. When the serialization process
 * fills up the buffer:
 * - if a callback is not provided, a value equal to or greater than @p
 *   data_size is returned;
 * - if a callback is provided, it is invoked with the user-defined context.
 *
 * The callback is responsible for handling the data chunk (e.g., copying it
 * elsewhere). If the callback returns `false`, the process is aborted and the
 * function returns the number of bytes written up to that point.
 *
 * When the serialization process is completed successfully, the output buffer
 * contains a null-terminated string and the callback is called, if any.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] module
 *     The module to serialize.
 * @param[in] with_submodules
 *     Flag indicating whether submodules should be (recursively) serialized.
 * @param[in] callback
 *     Optional callback function invoked whenever the buffer is full or the
 *     serialization process is completed.
 * @param[in] user_data
 *     User-defined context passed to the callback.
 * @param[out] data
 *     The buffer where the serialized model will be stored.
 * @param[in] data_size
 *     The size of the data buffer.
 * @return
 *     - The total number of bytes written, including the terminating null byte,
 *       upon successful completion;
 *     - a value equal to or greater than @p data_size, if no callback is
 *       provided and the serialized model was truncated;
 *     - the accumulated number of bytes for all successful calls of the
 *       @p callback, if the @p callback eventually requests to stop;
 *     - `-1` in case of error.
 *
 * @sa
 * - @ref nuxmv_serialize_model_to_string()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.002
 */
int nuxmv_serialize_module_to_string(nuxmv_env env, nuxmv_module module,
                                     bool with_submodules,
                                     nuxmv_serialized_chunk_callback callback,
                                     void *user_data, char *data,
                                     size_t data_size);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_model Models
 *
 * @brief Functions for handling Models
 */
///@{

/**
 * @brief Valid model
 *
 * This macro checks whether @p model is a valid @ref nuxmv_model.
 *
 * @param[in] model
 *     The model to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_MODEL(model) ((model).repr != NULL)

/**
 * @brief Create a new model instantiating a module with the desired parameters
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] module
 *     The module to instantiate into a model. The module must not be destroyed
 *     while the model is still in use.
 * @param[in] params
 *     A list of parameters for the model.
 *     If no list shall be used it is safe to use NULL or the
 *     result of malloc(0), provided that param_num=0.
 * @param[in] param_num
 *     The number of parameters in the list. If no list shall be passed,
 *     use 0 as actual value of param_num.
 * @return
 *     The newly created model. In case of error, @ref NUXMV_VALID_MODEL()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_create_model_from_string()
 * - @ref nuxmv_model_get_state_var()
 * - @ref nuxmv_destroy_model()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.009.03
 */
nuxmv_model nuxmv_create_model(nuxmv_env env, nuxmv_module module,
                               const nuxmv_expr *params, size_t param_num);

/**
 * @brief Create a model from a string
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] fmt
 *     The format of the input string.
 * @param[in] data
 *     A null-terminated string containing the model data.
 * @return
 *     The newly created model corresponding to the string. In case of error,
 *     @ref NUXMV_VALID_MODEL() evaluates to `false`.
 *
 * @note A current limitation of this function is that it always
 * returns a flattened model, consisting only of a single root module,
 * even if the input string contains submodules. We plan to remove
 * this limitation in future releases.
 *
 * @sa
 * - @ref nuxmv_create_model()
 * - @ref nuxmv_destroy_model()
 *
 * @req 03.005
 */
nuxmv_model nuxmv_create_model_from_string(nuxmv_env env,
                                           nuxmv_model_format fmt,
                                           const char *data);

/**
 * @brief Serialize a model to a string
 *
 * This function converts the given model into a string representation using the
 * specified format.
 *
 * The output is written to the provided buffer. When the serialization process
 * fills up the buffer:
 * - if a callback is not provided, a value equal to or greater than @p
 *   data_size is returned;
 * - if a callback is provided, it is invoked with the user-defined context.
 *
 * The callback is responsible for handling the data chunk (e.g., copying it
 * elsewhere). If the callback returns `false`, the process is aborted and the
 * function returns the number of bytes written up to that point.
 *
 * When the serialization process is completed successfully, the output buffer
 * contains a null-terminated string and the callback is called, if any.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to serialize.
 * @param[in] fmt
 *     The format to use for serialization.
 * @param[in] callback
 *     Optional callback function invoked whenever the buffer is full or the
 *     serialization process is completed.
 * @param[in] user_data
 *     User-defined context passed to the callback.
 * @param[out] data
 *     The buffer where the serialized model will be stored.
 * @param[in] data_size
 *     The size of the data buffer.
 * @return
 *     - The total number of bytes written, including the terminating null byte,
 *       upon successful completion;
 *     - a value equal to or greater than @p data_size, if no callback is
 *       provided and the serialized model was truncated;
 *     - the accumulated number of bytes for all successful calls of the
 *       @p callback, if the @p callback eventually requests to stop;
 *     - `-1` in case of error.
 *
 * @sa
 * - @ref nuxmv_create_model_from_string()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.002
 */
int nuxmv_serialize_model_to_string(nuxmv_env env, nuxmv_model model,
                                    nuxmv_model_format fmt,
                                    nuxmv_serialized_chunk_callback callback,
                                    void *user_data, char *data,
                                    size_t data_size);

/**
 * @brief Check the given property on a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] property
 *     The property to check.
 * @param[in] model
 *     A model to check the property on.
 * @param[in] opts
 *     A list of options for the check.
 *     If no list shall be used it is safe to use NULL or the
 *     result of malloc(0), provided that opt_num=0.
 * @param[in] opt_num
 *     The number of options in the list. If no list shall be passed,
 *     use 0 as actual value of opt_num.
 * @return
 *     The result of the checking. In case of error, @ref NUXMV_VALID_RESULT()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 02.001
 */
nuxmv_result nuxmv_model_check_property(nuxmv_env env, nuxmv_model model,
                                        nuxmv_property property,
                                        const nuxmv_opt *opts, size_t opt_num);

/**
 * @brief Check for deadlock freedom
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     A model to check the deadlock on.
 * @param[in] opts
 *     A list of options for the check.
 * @param[in] opt_num
 *     The number of options in the list. If no list shall be passed,
 *     use 0 as actual value of opt_num.
 * @return
 *     The result of the checking. In case of error, @ref
 *     NUXMV_VALID_RESULT() evaluates to `false`.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_property_check_satisfiability()
 * - @ref nuxmv_simulation_get_result()
 * - @ref nuxmv_trace_check_property()
 * - @ref nuxmv_model_check_receptiveness()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 02.005
 *
 * @unimplemented
 */
nuxmv_result nuxmv_model_check_deadlock(nuxmv_env env, nuxmv_model model,
                                        const nuxmv_opt *opts, size_t opt_num);

/**
 * @brief Check for receptiveness to inputs
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     A model to check the deadlock on.
 * @param[in] opts
 *     A list of options for the check.
 *     If no list shall be used it is safe to use NULL or the
 *     result of malloc(0), provided that opt_num=0.
 * @param[in] opt_num
 *     The number of options in the list. If no list shall be passed,
 *     use 0 as actual value of opt_num.
 * @return
 *     The result of the checking. In case of error, @ref
 *     NUXMV_VALID_RESULT() evaluates to `false`.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_simulation_get_result()
 * - @ref nuxmv_trace_check_property()
 * - @ref nuxmv_model_check_deadlock()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req ??
 *
 * @unimplemented
 */
nuxmv_result nuxmv_model_check_receptiveness(nuxmv_env env, nuxmv_model model,
                                             const nuxmv_opt *opts,
                                             size_t opt_num);

/**
 * @brief Destroy a model
 *
 * With this function, the user notifies the environment that the selected
 * model is no more needed.
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] model
 *     A model to destroy.
 * @return
 *     `NUXMV_SUCCESS` if the module was destroyed,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_create_model()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.01
 */
nuxmv_status_code nuxmv_destroy_model(nuxmv_env env, nuxmv_model model);

///@}

/**
 * @brief Get the root module of a model.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to get the root module from.
 * @return
 *     The top-level module containing all submodules instances and variables.
 *
 * @req 03.004.02
 */
nuxmv_module nuxmv_model_get_root_module(nuxmv_env env, nuxmv_model model);

/** *************************************************************************
 * @defgroup nuxmv_group_model_get_vars Model Variable Getters
 * @ingroup nuxmv_group_model
 *
 * @brief Functions for getting Variables from a Model
 */
///@{

/**
 * @brief Get the number of state variables in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the state variable number from.
 * @return
 *     The number of state variables in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_state_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_state_var_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th state variable of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] var_idx
 *     The index of the state variable counting from 0.
 * @return
 *     The state variable of the model. In case of error, @ref
 *     NUXMV_VALID_VAR_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_state_var_num()
 * - @ref nuxmv_module_get_state_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_var_decl nuxmv_model_get_state_var(nuxmv_env env, nuxmv_model model,
                                         int var_idx);

/**
 * @brief Get the number of input variables in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the input variable number from.
 * @return
 *     The number of input variables in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_input_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_input_var_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th input variable of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] var_idx
 *     The index of the input variable counting from 0.
 * @return
 *     The input variable of the model. In case of error, @ref
 *     NUXMV_VALID_VAR_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_input_var_num()
 * - @ref nuxmv_module_get_input_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_var_decl nuxmv_model_get_input_var(nuxmv_env env, nuxmv_model model,
                                         int var_idx);

/**
 * @brief Get the number of frozen variables in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the frozen variable number from.
 * @return
 *     The number of frozen variables in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_frozen_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_frozen_var_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th frozen variable of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] var_idx
 *     The index of the frozen variable counting from 0.
 * @return
 *     The frozen variable of the model. In case of error, @ref
 *     NUXMV_VALID_VAR_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_frozen_var_num()
 * - @ref nuxmv_module_get_frozen_var()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_var_decl nuxmv_model_get_frozen_var(nuxmv_env env, nuxmv_model model,
                                          int var_idx);

/**
 * @brief Get the number of user-defined function declarations in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the function declaration number from.
 * @return
 *     The number of function declarations in the model or `-1` in case of
 *     error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_function()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req ??
 */
int nuxmv_model_get_function_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th user-defined function declaration of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] fun_idx
 *     The index of the function declaration counting from 0.
 * @return
 *     The function declaration of the model. In case of error, @ref
 *     NUXMV_VALID_FUN_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_function_num()
 * - @ref nuxmv_module_get_function()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req ??
 */
nuxmv_fun_decl nuxmv_model_get_function(nuxmv_env env, nuxmv_model model,
                                        int fun_idx);

/**
 * @brief Get the number of initial constraints in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the initial constraint number from.
 * @return
 *     The number of initial constraints in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_init()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_init_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th initial constraint of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] init_idx
 *     The index of the initial constraint counting from 0.
 * @return
 *     The initial constraint of the model. In case of error, @ref
 *     NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_init_num()
 * - @ref nuxmv_module_get_init()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_expr nuxmv_model_get_init(nuxmv_env env, nuxmv_model model, int init_idx);

/**
 * @brief Get the number of transition constraints in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the transition constraint number from.
 * @return
 *     The number of transition constraints in the model or `-1` in case of
 *     error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_trans()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_trans_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th transition constraint of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] trans_idx
 *     The index of the transition constraint counting from 0.
 * @return
 *     The transition constraint of the model. In case of error, @ref
 *     NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_trans_num()
 * - @ref nuxmv_module_get_trans()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_expr nuxmv_model_get_trans(nuxmv_env env, nuxmv_model model,
                                 int trans_idx);

/**
 * @brief Get the number of invariant constraints in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the invariant constraint number from.
 * @return
 *     The number of invariant constraints in the model or `-1` in case of
 * error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_invar()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_invar_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th invariant constraint of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] invar_idx
 *     The index of the invariant constraint counting from 0.
 * @return
 *     The invariant constraint of the model. In case of error, @ref
 *     NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_invar_num()
 * - @ref nuxmv_module_get_invar()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_expr nuxmv_model_get_invar(nuxmv_env env, nuxmv_model model,
                                 int invar_idx);

/**
 * @brief Get the number of justice constraints in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the justice constraint number from.
 * @return
 *     The number of justice constraints in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_justice()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_justice_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th justice constraint of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] just_idx
 *     The index of the justice constraint counting from 0.
 * @return
 *     The justice constraint of the model. In case of error, @ref
 *     NUXMV_VALID_EXPR() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_justice_num()
 * - @ref nuxmv_module_get_justice()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_expr nuxmv_model_get_justice(nuxmv_env env, nuxmv_model model,
                                   int just_idx);

/**
 * @brief Get the number of compassions in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the compassion number from.
 * @return
 *     The number of compassions in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_compassion()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_compassion_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th compassion of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] comp_idx
 *     The index of the compassion counting from 0.
 * @return
 *     The compassion of the model. In case of error, @ref
 *     NUXMV_VALID_COMPASSION() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_compassion_num()
 * - @ref nuxmv_module_get_compassion()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_compassion nuxmv_model_get_compassion(nuxmv_env env, nuxmv_model model,
                                            int comp_idx);

/**
 * @brief Get the number of define declarations in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the define declaration number from.
 * @return
 *     The number of define declarations in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_define()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_define_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th define declaration of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] def_idx
 *     The index of the define declaration counting from 0.
 * @return
 *     The define declaration of the model. In case of error, @ref
 *     NUXMV_VALID_DEFINE_DECL() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_define_num()
 * - @ref nuxmv_module_get_define()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_define_decl nuxmv_model_get_define(nuxmv_env env, nuxmv_model model,
                                         int def_idx);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_model_get_assigns Model Assign Getters
 * @ingroup nuxmv_group_model
 *
 * @brief Functions for getting Assigns from a Model
 */
///@{

/**
 * @brief Get the number of initial assignments in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the initial assignment number from.
 * @return
 *     The number of initial assignments in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_init_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_init_assign_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th initial assignment of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] assign_idx
 *     The index of the initial assignment counting from 0.
 * @return
 *     The initial assignment of the model. In case of error, @ref
 *     NUXMV_VALID_ASSIGN() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_init_assign_num()
 * - @ref nuxmv_module_get_init_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_assign nuxmv_model_get_init_assign(nuxmv_env env, nuxmv_model model,
                                         int assign_idx);

/**
 * @brief Get the number of next assignments in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the next assignment number from.
 * @return
 *     The number of next assignments in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_next_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_next_assign_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th next assignment of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] assign_idx
 *     The index of the next assignment counting from 0.
 * @return
 *     The next assignment of the model. In case of error, @ref
 *     NUXMV_VALID_ASSIGN() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_next_assign_num()
 * - @ref nuxmv_module_get_next_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_assign nuxmv_model_get_next_assign(nuxmv_env env, nuxmv_model model,
                                         int assign_idx);

/**
 * @brief Get the number of invariant assignments in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the invariant assignment number from.
 * @return
 *     The number of invariant assignments in the model or `-1` in case of
 * error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_next_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_invar_assign_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th invariant assignment of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] assign_idx
 *     The index of the invariant assignment counting from 0.
 * @return
 *     The invariant assignment of the model. In case of error, @ref
 *     NUXMV_VALID_ASSIGN() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_invar_assign_num()
 * - @ref nuxmv_module_get_invar_assign()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_assign nuxmv_model_get_invar_assign(nuxmv_env env, nuxmv_model model,
                                          int assign_idx);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_model_get_properties Model Property Getters
 * @ingroup nuxmv_group_model
 *
 * @brief Functions for getting Properties from a Model
 */
///@{

/**
 * @brief Get the number of properties in a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to extract the property number from.
 * @return
 *     The number of properties in the model or `-1` in case of error.
 *
 * @note
 * Should the environment or the model be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_model_get_property()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
int nuxmv_model_get_property_num(nuxmv_env env, nuxmv_model model);

/**
 * @brief Get the *i*-th property of a model
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] prop_idx
 *     The index of the property counting from 0.
 * @return
 *     The property of the model. In case of error, @ref NUXMV_VALID_PROPERTY()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_property_num()
 * - @ref nuxmv_model_get_property_by_name()
 * - @ref nuxmv_module_add_property()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.004.02
 */
nuxmv_property nuxmv_model_get_property(nuxmv_env env, nuxmv_model model,
                                        int prop_idx);

/**
 * @brief Get the property of a model by name
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] model
 *     The model to inspect.
 * @param[in] name
 *     The name of the property.
 * @return
 *     The property of the model. In case of error, @ref NUXMV_VALID_PROPERTY()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_model_get_property()
 * - @ref nuxmv_module_add_property()
 *
 * @req 03.004.02
 */
nuxmv_property nuxmv_model_get_property_by_name(nuxmv_env env,
                                                nuxmv_model model,
                                                const char *name);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_model_add_property Add property to Model
 * @ingroup nuxmv_group_model
 *
 * @brief Functions for adding Properties to a Model
 */
///@{
/**
 * @brief Add a property to the model
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] model
 *     The model to modify.
 * @param[in] property
 *     A property to add to the model.
 * @return
 *     `NUXMV_SUCCESS` if the invariant assignment was added,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @req 03.004.02
 */
nuxmv_status_code nuxmv_model_add_property(nuxmv_env env, nuxmv_model model,
                                           nuxmv_property property);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_property Properties
 *
 * @brief Functions for handling Properties
 */
///@{

/**
 * @brief Valid property
 *
 * This macro checks whether @p property is a valid @ref nuxmv_property.
 *
 * @param[in] property
 *     The property to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_PROPERTY(property) ((property).repr != NULL)

/**
 * @brief Create a new property
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] type
 *     The type of the property to create.
 * @param[in] expr
 *     An expression to attach the property to.
 * @param[in] name
 *     The name of the property as a null-terminated string.
 *     name is optional, use NULL as no-value.
 * @return
 *     The newly created property. In case of error, @ref
 *     NUXMV_VALID_PROPERTY() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_property_from_string()
 * - @ref nuxmv_module_add_property()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.008
 */
nuxmv_property nuxmv_make_property(nuxmv_env env, nuxmv_property_type type,
                                   nuxmv_expr expr, const char *name);

/**
 * @brief Create a property from string
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] name
 *     The name of the property as a null-terminated string.
 *     name is optional, use NULL as no-value.
 * @param[in] type
 *     The type of the property to create.
 * @param[in] data
 *     A null-terminated string containing the property data.
 * @param[in] scope
 *     A context symbols belongs to.
 * @return
 *     The newly created property corresponding to the string. In case of error,
 *     @ref NUXMV_VALID_PROPERTY() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_make_property()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.005
 */
nuxmv_property nuxmv_make_property_from_string(nuxmv_env env,
                                               nuxmv_property_type type,
                                               const char *data,
                                               nuxmv_module scope,
                                               const char *name);

/**
 * @brief Create the satisfiability of a property
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] property
 *     The property to check the satisfiability of.
 * @param[in] opts
 *     A list of options to apply.
 *     If no list shall be used it is safe to use NULL or the
 *     result of malloc(0), provided that opt_num=0.
 * @param[in] opt_num
 *     The number of options in the list. If no list shall be passed,
 *     use 0 as actual value of opt_num.
 * @return
 *     The result of the simulation. In case of error, @ref
 *     NUXMV_VALID_RESULT() evaluates to `false`.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_property_check_satisfiability()
 * - @ref nuxmv_simulation_get_result()
 * - @ref nuxmv_trace_check_property()
 * - @ref nuxmv_model_check_deadlock()
 * - @ref nuxmv_model_check_receptiveness()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 02.003
 *
 * @unimplemented
 */
nuxmv_result nuxmv_property_check_satisfiability(nuxmv_env env,
                                                 nuxmv_property property,
                                                 const nuxmv_opt *opts,
                                                 size_t opt_num);
/**
 * @brief Get the expression of a property.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] property
 *     The property to check the satisfiability of.
 * @return
 *     The expression of the property
 *
 * @req 02.003
 */
nuxmv_expr nuxmv_property_get_expr(nuxmv_env env, nuxmv_property property);

/**
 * @brief Get the name of a property.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] property
 *     The property to check the satisfiability of.
 * @return
 *     The name of the property, NULL if the property doesn't have a name.
 *
 * @req 02.003
 */
const char *nuxmv_property_get_name(nuxmv_env env, nuxmv_property property);

/**
 * @brief Get the type of a property.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] property
 *     The property to check the satisfiability of.
 * @return
 *     The type of the property
 *
 * @req 02.003
 */
nuxmv_property_type nuxmv_property_get_type(nuxmv_env env,
                                            nuxmv_property property);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_simulation Simulation
 *
 * @brief Functions for handling Simulations
 */
///@{

/**
 * @brief Valid simulation
 *
 * This macro checks whether @p simulation is a valid @ref nuxmv_simulation.
 *
 * @param[in] simulation
 *     The simulation to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_SIMULATION(simulation) ((simulation).repr != NULL)

/**
 * @brief Helper macro to construct a simulation constraint
 *
 * @param[in] simple_constraint_
 *     An @ref nuxmv_expr.
 * @param[in] trans_constraint_
 *     An @ref nuxmv_expr.
 * @param[in] trace_
 *     An @ref nuxmv_trace.
 * @param[in] trace_start_
 *     An integer representing the starting step of the trace.
 * @param[in] ltl_formula_
 *     An @ref nuxmv_expr.
 */
#define NUXMV_MAKE_SIMULATION_CONSTRAINT(                                      \
    simple_constraint_, trans_constraint_, trace_, trace_start_, ltl_formula_) \
    ((nuxmv_simulation_constraint){.simple_constraint = (simple_constraint_),  \
                                   .trans_constraint = (trans_constraint_),    \
                                   .trace = (trace_),                          \
                                   .trace_start = (trace_start_),              \
                                   .ltl_formula = (ltl_formula_)})

/**
 * @brief Create a new simulation for a model
 *
 * When no longer needed, the simulation can be freed using
 * @ref nuxmv_destroy_simulation().
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] model
 *     The model to simulate.
 * @param[in] constraint
 *     The constraint to apply to the simulation.
 * @param[in] opts
 *     A list of options to apply.
 *     If no list shall be used it is safe to use NULL or the
 *     result of malloc(0), provided that opt_num=0.
 * @param[in] opt_num
 *     The number of options in the list. If no list shall be passed,
 *     use 0 as actual value of opt_num.
 * @return
 *     The newly created simulation. In case of error, @ref
 *     NUXMV_VALID_SIMULATION() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_extend_simulation()
 * - @ref nuxmv_simulation_get_result()
 * - @ref nuxmv_destroy_simulation()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 02.002
 *
 * @unimplemented
 */
nuxmv_simulation nuxmv_create_simulation(nuxmv_env env, nuxmv_model model,
                                         nuxmv_simulation_constraint constraint,
                                         const nuxmv_opt *opts, size_t opt_num);

/**
 * @brief Destroy a simulation
 *
 * With this function, the user notifies the environment that the selected
 * simulation is no more needed.
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] simulation
 *     A simulation to destroy.
 * @return
 *     `NUXMV_SUCCESS` if the simulation was destroyed,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_create_simulation()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 02.002
 *
 * @unimplemented
 */
nuxmv_status_code nuxmv_destroy_simulation(nuxmv_env env,
                                           nuxmv_simulation simulation);

/**
 * @brief Extend the simulation by *k* steps
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in,out] simulation
 *     The simulation to extend.
 * @param[in] k
 *     The number of steps to extend the simulation by.
 * @param[in] constraint
 *     The constraint to apply to the simulation.
 * @return
 *     `NUXMV_SUCCESS` if the simulation was extended,
 *     `NUXMV_FAILURE` in case of error.
 *
 * @sa
 * - @ref nuxmv_create_simulation()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 02.002
 *
 * @unimplemented
 */
nuxmv_status_code
nuxmv_extend_simulation(nuxmv_env env, nuxmv_simulation simulation, size_t k,
                        nuxmv_simulation_constraint constraint);

/**
 * @brief Get the result out of a simulation
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] simulation
 *     The simulation to inspect.
 * @return
 *     The result of the simulation. In case of error, @ref
 *     NUXMV_VALID_RESULT() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_property_check_satisfiability()
 * - @ref nuxmv_trace_check_property()
 * - @ref nuxmv_model_check_deadlock()
 * - @ref nuxmv_model_check_receptiveness()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 02.002
 *
 * @unimplemented
 */
nuxmv_result nuxmv_simulation_get_result(nuxmv_env env,
                                         nuxmv_simulation simulation);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_result Results
 *
 * @brief Functions for handling simulation Results
 */
///@{

/**
 * @brief Valid result
 *
 * This macro checks whether @p result is a valid @ref nuxmv_result.
 *
 * @param[in] result
 *     The result to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_RESULT(result) ((result).repr != NULL)

/**
 * @brief Get the code out of a result
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] result
 *     The result to inspect.
 * @return
 *     The code of the result or @ref NUXMV_RESULT_INVALID in case of error.
 *
 * @sa
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 02.001
 */
nuxmv_result_code nuxmv_result_get_code(nuxmv_env env, nuxmv_result result);

/**
 * @brief Get the trace stored in a nuxmv_result
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] result
 *     The result to inspect.
 * @return
 *     The trace contained in the result. In case of error, @ref
 *     NUXMV_VALID_TRACE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_trace_get_step_num()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
nuxmv_trace nuxmv_result_get_trace(nuxmv_env env, nuxmv_result result);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_trace Traces
 *
 * @brief Functions for handling Traces
 */
///@{

/**
 * @brief Valid trace type
 *
 * This macro checks whether @p trace is a valid @ref nuxmv_trace.
 *
 * @param[in] trace
 *     The trace to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 */
#define NUXMV_VALID_TRACE(trace) ((trace).repr != NULL)

/**
 * @brief Make a trace from string
 *
 * @param[in] env
 *     The environment to modify.
 * @param[in] fmt
 *     The format of the input string.
 * @param[in] data
 *     A null-terminated string containing the trace data.
 * @param[in] model
 *     A model to attach the trace to.
 * @return
 *     The newly created trace corresponding to the string. In case of error,
 *     @ref NUXMV_VALID_TRACE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_trace_get_step_num()
 * - @ref nuxmv_trace_get_function()
 * - @ref nuxmv_trace_get_loopback()
 * - @ref nuxmv_result_get_trace()
 * - @ref nuxmv_serialize_trace_to_string()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.005
 */
nuxmv_trace nuxmv_make_trace_from_string(nuxmv_env env, nuxmv_trace_format fmt,
                                         const char *data, nuxmv_model model);

/**
 * @brief Serialize a trace to a string
 *
 * This function converts the given trace into a string representation using the
 * specified format.
 *
 * The output is written to the provided buffer. When the serialization process
 * fills up the buffer:
 * - if a callback is not provided, a value equal to or greater than @p
 *   data_size is returned;
 * - if a callback is provided, it is invoked with the user-defined context.
 *
 * The callback is responsible for handling the data chunk (e.g., copying it
 * elsewhere). If the callback returns `false`, the process is aborted and the
 * function returns the number of bytes written up to that point.
 *
 * When the serialization process is completed successfully, the output buffer
 * contains a null-terminated string and the callback is called, if any.
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to serialize.
 * @param[in] fmt
 *     The format to use for serialization.
 * @param[in] callback
 *     Optional callback function invoked whenever the buffer is full or the
 *     serialization process is completed.
 * @param[in] user_data
 *     User-defined context passed to the callback.
 * @param[out] data
 *     The buffer where the serialized model will be stored.
 * @param[in] data_size
 *     The size of the data buffer.
 * @return
 *     - The total number of bytes written, including the terminating null byte,
 *       upon successful completion;
 *     - a value equal to or greater than @p data_size, if no callback is
 *       provided and the serialized trace was truncated;
 *     - the accumulated number of bytes for all successful calls of the
 *       @p callback, if the @p callback eventually requests to stop;
 *     - `-1` in case of error.
 *
 * @sa
 * - @ref nuxmv_result_get_trace()
 * - @ref nuxmv_make_trace_from_string()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
int nuxmv_serialize_trace_to_string(nuxmv_env env, nuxmv_trace trace,
                                    nuxmv_trace_format fmt,
                                    nuxmv_serialized_chunk_callback callback,
                                    void *user_data, char *data,
                                    size_t data_size);

/**
 * @brief Check a property on a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] property
 *     The property to check.
 * @param[in] trace
 *     A trace to check the property on.
 * @param[in] model
 *     A model for the trace.
 * @param[in] opts
 *     A list of options for the check.
 *     If no list shall be used it is safe to use NULL or the
 *     result of malloc(0), provided that opt_num=0.
 * @param[in] opt_num
 *     The number of options in the list. If no list shall be passed,
 *     use 0 as actual value of opt_num.
 * @return
 *     The result of the checking. In case of error, @ref
 *     NUXMV_VALID_RESULT() evaluates to `false`.
 *
 * @sa
 * - @ref NUXMV_COUNT_OF()
 * - @ref nuxmv_property_check_satisfiability()
 * - @ref nuxmv_simulation_get_result()
 * - @ref nuxmv_model_check_deadlock()
 * - @ref nuxmv_model_check_receptiveness()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 02.006
 *
 * @unimplemented
 */
nuxmv_result nuxmv_trace_check_property(nuxmv_env env, nuxmv_trace trace,
                                        nuxmv_property property,
                                        nuxmv_model model,
                                        const nuxmv_opt *opts, size_t opt_num);

///@}

/** *************************************************************************
 * @defgroup nuxmv_group_trace_get Trace Getters
 * @ingroup nuxmv_group_trace
 *
 * @brief Functions for getting information out of a Trace
 */
///@{

/**
 * @brief Valid trace value
 *
 * This macro checks whether @p symb_val is a valid @ref nuxmv_trace_value.
 *
 * @param[in] symb_val
 *     The symbol value to inspect.
 * @return
 *     `true` if the option is valid, `false` otherwise.
 *
 * @sa
 * - @ref NUXMV_MAKE_OPT()
 */
#define NUXMV_VALID_TRACE_VALUE(symb_val)                                      \
    (NUXMV_VALID_EXPR((symb_val).identifier) &&                                \
     NUXMV_VALID_EXPR((symb_val).value))

/**
 * @brief Get the number of steps in a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to inspect.
 * @return
 *     The number of steps in the trace or `-1` in case of error.
 *
 * @sa
 * - @ref nuxmv_trace_get_step_state()
 * - @ref nuxmv_trace_get_step_input()
 * - @ref nuxmv_trace_get_step_define()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
int nuxmv_trace_get_step_num(nuxmv_env env, nuxmv_trace trace);

/**
 * @brief Get the number of state variables in a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to extract the state variable number from.
 * @param[in] step_idx
 *     The index of the step to inspect counting from 0.
 * @return
 *     The number of state variables in the trace or `-1` in case of error.
 *
 * @note
 * Should the environment or the trace be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_trace_get_step_state()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
int nuxmv_trace_get_step_state_num(nuxmv_env env, nuxmv_trace trace,
                                   int step_idx);

/**
 * @brief Get the value of a state variable from the *i*-th step of a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to inspect.
 * @param[in] step_idx
 *     The index of the step to inspect counting from 0.
 * @param[in] var_idx
 *     The index of the state variable counting from 0.
 * @return
 *     The value of the state variable in the trace. In case of error, @ref
 *     NUXMV_VALID_TRACE_VALUE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_trace_get_step_num()
 * - @ref nuxmv_trace_get_step_state_num()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
nuxmv_trace_value nuxmv_trace_get_step_state(nuxmv_env env, nuxmv_trace trace,
                                             int step_idx, int var_idx);

/**
 * @brief Get the number of input variables in a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to extract the input variable number from.
 * @param[in] step_idx
 *     The index of the step to inspect counting from 0.
 * @return
 *     The number of input variables in the trace or `-1` in case of error.
 *
 * @note
 * Should the environment or the trace be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_trace_get_step_input()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
int nuxmv_trace_get_step_input_num(nuxmv_env env, nuxmv_trace trace,
                                   int step_idx);

/**
 * @brief Get the value of an input variable from the *i*-th step of a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to inspect.
 * @param[in] step_idx
 *     The index of the step to inspect counting from 0.
 * @param[in] var_idx
 *     The index of the input variable counting from 0.
 * @return
 *     The input variable of the trace. In case of error, @ref
 *     NUXMV_VALID_TRACE_VALUE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_trace_get_step_num()
 * - @ref nuxmv_trace_get_step_input_num()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
nuxmv_trace_value nuxmv_trace_get_step_input(nuxmv_env env, nuxmv_trace trace,
                                             int step_idx, int var_idx);

/**
 * @brief Get the number of defines in a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to extract the define number from.
 * @param[in] step_idx
 *     The index of the step to inspect counting from 0.
 * @return
 *     The number of defines in the trace or `-1` in case of error.
 *
 * @note
 * Should the environment or the trace be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_trace_get_step_define()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
int nuxmv_trace_get_step_define_num(nuxmv_env env, nuxmv_trace trace,
                                    int step_idx);

/**
 * @brief Get the value of a define from the *i*-th step of a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to inspect.
 * @param[in] step_idx
 *     The index of the step to inspect counting from 0.
 * @param[in] def_idx
 *     The index of the define counting from 0.
 * @return
 *     The define of the trace. In case of error, @ref NUXMV_VALID_TRACE_VALUE()
 *     evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_trace_get_step_num()
 * - @ref nuxmv_trace_get_step_define_num()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
nuxmv_trace_value nuxmv_trace_get_step_define(nuxmv_env env, nuxmv_trace trace,
                                              int step_idx, int def_idx);

/**
 * @brief Get the number of uninterpreted functions in a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to extract the uninterpreted function number from.
 * @return
 *     The number of uninterpreted functions in the trace or `-1` in case of
 *     error.
 *
 * @note
 * Should the environment or the trace be modified, the returned number is no
 * longer valid and shall be discarded.
 *
 * @sa
 * - @ref nuxmv_trace_get_function()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
int nuxmv_trace_get_function_num(nuxmv_env env, nuxmv_trace trace);

/**
 * @brief Get the value of a uninterpreted function from a trace
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to inspect.
 * @param[in] fun_idx
 *     The index of the uninterpreted function counting from 0.
 * @return
 *     The uninterpreted function of the trace. In case of error, @ref
 *     NUXMV_VALID_TRACE_VALUE() evaluates to `false`.
 *
 * @sa
 * - @ref nuxmv_trace_get_function_num()
 * - @ref nuxmv_module_get_function()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
nuxmv_trace_value nuxmv_trace_get_function(nuxmv_env env, nuxmv_trace trace,
                                           int fun_idx);

/**
 * @brief Get the the step the trace loops back, if any
 *
 * @param[in] env
 *     The environment to inspect.
 * @param[in] trace
 *     The trace to inspect.
 * @return
 *     The number of the step, counting from 0, the trace jumps back to; -1 in
 *     case of error; -2 if trace didn't loop.
 *
 * @sa
 * - @ref nuxmv_make_trace_from_string()
 * - @ref nuxmv_env_get_last_error_message()
 *
 * @req 03.007
 */
int nuxmv_trace_get_loopback(nuxmv_env env, nuxmv_trace trace);

///@}
#ifdef __cplusplus
}
#endif
